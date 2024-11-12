# user_session.py

import asyncio
import logging
from datetime import datetime
from database import save_messages, save_chat_preferences, get_chat_preferences, add_summary
from nlp import NLP
from test_project import eval
from UC import UC as uc


class UserSession:
    def __init__(self, chat_id):
        # Identificatore della chat e impostazioni iniziali
        self.chat_id = chat_id
        #self.messages = []  # Messaggi temporanei per l'analisi

        self.messages,self.current_summary = [],""

        self.daily_messages = []  # Messaggi giornalieri per il salvataggio nel database
        self.preferences = {
            "Auto-Riassunto": True,
            "Lingua": "it",
            "Filtro": "",
            "Lunghezza Riassunto": "medio",
        }
        self.nlp = NLP()
        self.max_time = 3 * 60  # Timer riassunto in secondi
        self.max_messages = 10  # Numero massimo di messaggi per riassunto

        # Gestione asincrona delle risorse
        self.timer_task = None
        self.lock = asyncio.Lock()
        self.pending_filters = []

    # Creazione asincrona dell'istanza UserSession
    @classmethod
    async def create(cls, chat_id):
        self = cls(chat_id)
        await self.load_session()
        return self

    # Timer per il riassunto automatico
    async def start_timer(self):
        if self.timer_task:
            self.timer_task.cancel()
        self.timer_task = asyncio.create_task(self._run_timer())

    async def _run_timer(self):
        start_time = datetime.now().timestamp()
        try:
            while True:
                elapsed_time = datetime.now().timestamp() - start_time
                if elapsed_time >= self.max_time:
                    break
                await asyncio.sleep(1)
            await self.analyze_messages()
        except asyncio.CancelledError:
            pass

    # Aggiunta di un nuovo messaggio e gestione del limite di messaggi
    async def add_message(self, username, message_type, content, timestamp, caption):
        async with self.lock:
            if await self.is_pending_filter(username):
                return

            message = {
                'username': username,
                'type': message_type,
                'content': content,
                'timestamp': datetime.fromtimestamp(timestamp),
                'caption': caption
            }
            self.messages.append(message)
            self.daily_messages.append(message)

            if len(self.messages) >= self.max_messages:
                if self.timer_task:
                    self.timer_task.cancel()
                await self.analyze_messages()
            else:
                await self.start_timer()

    # Analisi e riassunto dei messaggi
    async def analyze_messages(self):
        if not self.messages:
            logging.warning("Nessun messaggio da analizzare.")
            return
        eval.start("Summarizer")
        try:
            result = await self.nlp.process_messages(self.messages, self.current_summary, self.preferences)
            eval.stop("Summarizer")
            eval.print_results()

            self.current_summary = result
            self.messages = []
        except Exception as e:
            logging.error(f"Errore durante l'analisi dei messaggi: {e}")

    # Restituisce il riassunto corrente
    async def get_summary(self):
        if self.timer_task:
            self.timer_task.cancel()
        if len(self.messages)>0:
            await self.analyze_messages()
        if self.current_summary == "":
            return "Non c'è niente da riassumere" 
        return self.current_summary

    # Carica le preferenze della chat dal database
    async def load_session(self):
        db_preferences = get_chat_preferences(self.chat_id)
        if db_preferences:
            self.preferences.update(db_preferences)

    # Salvataggio dei messaggi e delle preferenze della sessione
    async def save_session(self):
        for message in self.daily_messages:
            save_messages(self.chat_id, message['username'], message['content'], message['type'], message['timestamp'], message['caption'])
        save_chat_preferences(self.chat_id, self.preferences["Auto-Riassunto"], self.preferences["Lingua"], self.preferences["Filtro"], self.preferences["Lunghezza Riassunto"])

    # Salvataggio e riassunto giornaliero
    async def daily_store(self):
        eval.start("Database")
        await self.save_session()
        if len(self.messages)>0:
            await self.analyze_messages()
        add_summary(self.chat_id, self.current_summary)

        eval.stop("Database")
        eval.print_results()

        self.daily_messages = []
        logging.info(f"Riassunto giornaliero per chat {self.chat_id} salvato.")

    # Gestione dei filtri in sospeso
    async def add_pending_filter(self, username):
        self.pending_filters.append(username)

    async def remove_pending_filter(self, username):
        if username in self.pending_filters:
            self.pending_filters.remove(username)

    async def is_pending_filter(self, username):
        return username in self.pending_filters

    # Gestione delle Preferenze
    async def get_preference(self, key):
        async with self.lock:
            return self.preferences.get(key, None)

    async def update_preference(self, key, value):
        async with self.lock:
            if key in self.preferences:
                self.preferences[key] = value
            else:
                logging.warning(f"Tentativo di aggiornamento di una preferenza non esistente: '{key}'")

