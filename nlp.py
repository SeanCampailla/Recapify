#nlp.py

import asyncio
import base64
import logging
import os

import cv2
import httpx
import openai
from config import Config
from moviepy.editor import VideoFileClip
from test_project import SummaryEvaluator, eval
from unstructured.partition.auto import partition

import shutil
import aiofiles


# Configura il logger
logger = logging.getLogger("nlp_logger")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Decoratore per il backoff
def backoff_decorator(retries=5, base_delay=1, max_delay=16):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt < retries - 1:
                        delay = min(base_delay * 2 ** attempt + random.uniform(0, 1), max_delay)
                        logger.warning(f"Errore: {e}, ritento tra {delay:.2f} secondi...")
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"Errore persistente dopo {retries} tentativi: {e}")
                        raise
        return wrapper
    return decorator

class NLP:
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=Config.OPENAI_API_KEY)
        self.summary = ""
        self.fidality = SummaryEvaluator(Config.OPENAI_API_KEY)

    async def process_messages(self, messages, context, preferences):
        #eval.start("Analyzer")
        print("questo è il contesto: ",context)
        tasks = []
        for message in messages:
            if message['type'] == 'text': self.summary += f"[{message['timestamp']}] {message['username']} ha inviato: {message['content']}\n"
            elif message['type'] in ["photo", "sticker"]: tasks.append(self._analyze_and_append(message, self.analyze_image, "ha inviato un'immagine"))
            elif message['type'] in ["voice", "audio"]: tasks.append(self._analyze_and_append(message, self.analyze_audio, "ha inviato un audio"))
            elif message['type'] in ['video', 'animation', 'video_note']: tasks.append(self._analyze_and_append(message, self.analyze_video, "ha inviato un video"))
            elif message['type'] == 'document': tasks.append(self._analyze_and_append(message, self.analyze_document, "ha inviato un documento"))
        await asyncio.gather(*tasks)
        #eval.stop("Analyzer")
        return await self.generate_summary(context,preferences)

    async def _analyze_and_append(self, message, analysis_func, description):
        result = await analysis_func(message)
        self.summary += f"[{message['timestamp']}] {message['username']} {description}: {result}\n"

    @backoff_decorator(retries=5, base_delay=1, max_delay=16)
    async def analyze_image(self, message):
        prompt = (
            f"Descrivi questa immagine in breve per inserirla in un contesto di chat. "
            f"{'Questa è una caption fornita dall’utente: ' + message['caption'] if message['caption'] else ''}"
            "\n\nDevi creare una descrizione concisa dell'immagine che possa essere integrata in un riassunto della conversazione."
        )
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": message["content"]}}]}],
                max_tokens=200,
            )
            #print (response.choices[0].message.content)
            return response.choices[0].message.content if response else ""
        except Exception as e:
            logger.error(f"Errore nell'analisi dell'immagine: {e}")
            return ""

    @backoff_decorator(retries=5, base_delay=1, max_delay=16)
    async def analyze_audio(self, message):
        audio_file_name = "audio_file.mp3"
        try:
            if message["content"].startswith("http://") or message["content"].startswith("https://"):
                await self.download_file(message["content"], audio_file_name)
            else:
                self.copy_local_file(message["content"], audio_file_name)

            with open(audio_file_name, "rb") as f:
                transcript_response = await self.client.audio.transcriptions.create(model="whisper-1", file=f, response_format="text")
            return transcript_response.strip() if transcript_response else ""
        except Exception as e:
            logger.error(f"Errore durante la trascrizione: {e}")
            return ""
        finally:
            if os.path.exists(audio_file_name):
                os.remove(audio_file_name)

    @backoff_decorator(retries=5, base_delay=1, max_delay=16)
    async def analyze_video(self, message):
        video_file_name = "temp_video.mp4"
        audio_file_name = "temp_audio.mp3"
        prompt = (
            "Analizza il contenuto visivo e, se presente, l'audio di questo video. "
            f"Descrivi il video brevemente in modo che possa essere compreso in un riassunto di una chat di gruppo. "
            f"{'Caption fornita dall’utente: ' + message['caption'] if message['caption'] else ''}"
        )
        try:
            # Scarica il file video
            if message["content"].startswith("http://") or message["content"].startswith("https://"):
                await self.download_file(message["content"], video_file_name)
            else:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, self.copy_local_file, message["content"], video_file_name)

            if not os.path.exists(video_file_name):
                raise FileNotFoundError(f"Il file video '{video_file_name}' non è stato creato correttamente.")

            # Verifica se il video contiene una traccia audio
            video_clip = VideoFileClip(video_file_name)
            has_audio = video_clip.audio is not None
            if has_audio:
                video_clip.audio.write_audiofile(audio_file_name)
            video_clip.close()

            # Leggi i fotogrammi del video
            video = cv2.VideoCapture(video_file_name)
            base64Frames = []
            while video.isOpened():
                success, frame = video.read()
                if not success:
                    break
                _, buffer = cv2.imencode(".jpg", frame)
                base64Frames.append(base64.b64encode(buffer).decode("utf-8"))
            video.release()

            # Crea i messaggi di prompt
            PROMPT_MESSAGES = [
                {
                    "role": "user",
                    "content": [
                        prompt,
                        *map(lambda x: {"image": x, "resize": 768}, base64Frames[0::60]),
                    ],
                },
            ]

            video_task = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=PROMPT_MESSAGES,
                max_tokens=200,
            )

            # Trascrizione dell'audio, se presente
            if has_audio:
                with open(audio_file_name, "rb") as f:
                    audio_task = self.client.audio.transcriptions.create(
                        model="whisper-1", file=f, response_format="text"
                    )
                    video_result, transcript_result = await asyncio.gather(video_task, audio_task)
            else:
                video_result, transcript_result = await asyncio.gather(video_task, None)

            # Estrai e processa i risultati
            video_description = video_result.choices[0].message.content.strip() if video_result else ""
            transcription = transcript_result.strip() if transcript_result else ""

            # Crea il riassunto finale
            if transcription:
                final_prompt = (
                    f"L'utente {message['username']} ha inviato un video con una descrizione e una trascrizione audio:\n"
                    f"Descrizione del video:\n{video_description}\n\n"
                    f"Trascrizione: {transcription}\n\n"
                    "Fornisci un riassunto che combini la descrizione del video e il contenuto del messaggio audio."
                )

                response = await self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": final_prompt}],
                    max_tokens=200,
                )
                combined_summary = response.choices[0].message.content.strip() if response else ""
                return combined_summary

            return video_description

        except Exception as e:
            logger.error(f"Errore durante l'analisi del video o dell'audio: {e}")
            return ""
        finally:
            # Rimuovi i file temporanei solo dopo il completamento delle operazioni
            if os.path.exists(video_file_name):
                os.remove(video_file_name)
            if os.path.exists(audio_file_name):
                os.remove(audio_file_name)

    @backoff_decorator(retries=5, base_delay=1, max_delay=16)
    async def analyze_document(self, message):
        prompt = (
            f"Analizza il seguente documento per estrarne i punti chiave. "
            f"{'Questa è una descrizione fornita dall’utente: ' + message['caption'] if message['caption'] else ''}"
            "\n\nDevi produrre una breve descrizione del documento per essere integrata in un riassunto di una conversazione di gruppo. "
            "Includi solo le informazioni principali, come argomenti trattati, conclusioni o dati rilevanti."
        )

        file_path = "temp_file"
        try:
            if message["content"].startswith("http://") or message["content"].startswith("https://"):
                await self.download_file(message["content"],file_path)
            else:
                self.copy_local_file(message["content"], file_path)

            document_content = self.extract_content(file_path)
            prompt = f"Riassumi brevemente questo documento:\n{document_content}"
            document_summary = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
            )
            return document_summary.choices[0].message.content if document_summary.choices else ""
        except Exception as e:
            logger.error(f"Errore nell'analisi del documento: {e}")
            return ""
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    def copy_local_file(self, file_url, file_path):
        if os.path.exists(file_url):
            shutil.copy(file_url, file_path)
        else:
            raise FileNotFoundError(f"Il file locale '{file_url}' non esiste.")

    async def download_file(self, file_url, file_path):
        async with httpx.AsyncClient() as client:
            response = await client.get(file_url)
            response.raise_for_status()
            with open(file_path, 'wb') as f:
                f.write(response.content)

    def extract_content(self, file_path):
        elements = partition(filename=file_path)
        return "\n".join([element.text for element in elements if element.text])

    async def generate_summary(self, context, preferences):
        #print(f"Questa è la chat analizzata:\n{self.summary} ")
        original_text = f"{context}\n{self.summary}" if context else self.summary
        language = preferences["Lingua"]
        length = preferences["Lunghezza Riassunto"]
        filter = preferences["Filtro"]

        # Definisce il numero di token in base alla lunghezza richiesta
        max_tokens = 150 if length == "breve" else 300 if length == "medio" else 600

        try:
            messages = self.create_summary_prompt(language, length, filter, context, self.summary)
            print("Testo analizzato: ",self.summary)
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=max_tokens
            )
            generated_summary = response.choices[0].message.content if response else ""
            result = await self.fidality.run_all_tests(generated_summary, original_text)
            self.summary = ""
            return generated_summary
        except Exception as e:
            logger.error(f"Errore nel riassunto: {e}")
            return ""

    def create_summary_prompt(self, language, length, filter, context, summary):
        """
        Genera un prompt personalizzato per riassumere una conversazione di gruppo.

        Parameters:
        - language: La lingua desiderata per il riassunto.
        - length: La lunghezza desiderata del riassunto ('breve', 'medio', 'lungo').
        - filter: Un filtro tematico specifico (opzionale).
        - context: Il contesto della conversazione (opzionale).
        - summary: Il testo della conversazione da riassumere.

        Returns:
        - Un prompt ottimizzato per la generazione del riassunto.
        """
        system_prompt = (
            "Sei un assistente AI specializzato nel riassumere conversazioni di chat di gruppo in modo conciso e informativo. "
            "Il tuo obiettivo è estrarre i punti chiave, evidenziare i contributi significativi di ciascun partecipante e identificare "
            "decisioni importanti, domande, risposte e cambiamenti emotivi rilevanti. "
            "Mantieni il tono naturale della conversazione e rispetta lo stile originale."
        )
        user_prompt = (
            f"Il seguente testo è una conversazione di chat di gruppo che necessita di essere riassunta.\n\n"
            f"**Lingua del riassunto:** {language}\n"
            f"**Lunghezza desiderata:** {length}\n"
            f"**Filtro tematico:** {filter if filter else 'Nessun filtro specifico'}\n\n"
            f"**Contesto della conversazione:**\n"
            f"{context if context else 'Nessun contesto specifico'}\n\n"
            f"**Conversazione:**\n"
            f"{summary}\n\n"
            "Per favore, riassumi la conversazione sopra riportata seguendo queste linee guida:\n\n"
            "- Utilizza la lingua specificata.\n"
            "- Se è presente un contesto usa anche quello per creare un riassunto ottimizzato ed attinente\n"
            "- Se è presente un filtro riassumi solo gli argomenti che parlano di quel tema\n"
            "- Mantieni uno stile che rispecchi il tono della chat originale.\n"
            "- Evidenzia i contributi significativi di ciascun partecipante.\n"
            "- Indica i momenti importanti, le decisioni chiave e i cambiamenti emotivi.\n"
            "- Sintetizza i temi o gli argomenti principali con dettagli concreti.\n"
            "- Mantieni il riassunto entro la lunghezza desiderata.\n"
            "-Analizza e riassumi i messaggi in ordine cronologico basato sui timestamp, mantenendo la sequenza temporale.\n\n"
            "Il tuo riassunto dovrebbe fornire una panoramica completa dell'interazione tra i partecipanti e dei principali argomenti discussi."
        )
        combined_prompt = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        return combined_prompt



