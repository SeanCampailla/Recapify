from datetime import datetime
import os

# Imposta il percorso della tua cartella multimediale
media_folder = os.path.join(".venv", "Multimedia")

class UC:
    @staticmethod
    def uc1():
        context = ""
        messages = [
            {'username': 'utente1', 'type': 'text', 'content': "Buongiorno a tutti! Qualcuno ha già preso un caffè?",'timestamp': datetime.now().timestamp(), 'caption': None},
            {'username': 'utente2', 'type': 'text', 'content': "Ciao! Sì, stamattina ero proprio stanco, quindi il caffè è stato obbligatorio.", 'timestamp': datetime.now().timestamp(), 'caption': None},
            {'username': 'utente1', 'type': 'text','content': "Capisco! Io invece sono ancora a casa, non mi sono nemmeno vestito.",'timestamp': datetime.now().timestamp(), 'caption': None},
            {'username': 'utente3', 'type': 'text','content': "Oggi pensavo di fare un'escursione in montagna, il tempo sembra perfetto.",'timestamp': datetime.now().timestamp(), 'caption': None},
            {'username': 'utente1', 'type': 'text','content': "Che bello! Avrei voluto unirmi ma ho troppi impegni. Prendete qualche foto?",'timestamp': datetime.now().timestamp(), 'caption': None},
            {'username': 'utente2', 'type': 'text','content': "Assolutamente! L'ultima volta che siamo andati c'era una vista spettacolare.",'timestamp': datetime.now().timestamp(), 'caption': None},
            {'username': 'utente3', 'type': 'text','content': "Se volete, vi mando delle foto del panorama. Sembra un quadro.",'timestamp': datetime.now().timestamp(), 'caption': None},
            {'username': 'utente1', 'type': 'text','content': "Per favore, sì! Mi piacerebbe vedere. Mi manca la montagna.",'timestamp': datetime.now().timestamp(), 'caption': None},
            {'username': 'utente2', 'type': 'text','content': "Anche io non vedo l'ora di tornarci. Dobbiamo organizzare una gita tutti insieme.",'timestamp': datetime.now().timestamp(), 'caption': None},
            {'username': 'utente3', 'type': 'text','content': "Perfetto, allora ci teniamo aggiornati e troviamo un weekend libero per tutti!",'timestamp': datetime.now().timestamp(), 'caption': None},
        ]
        return messages, context

    @staticmethod
    def uc2():
        context = ("Nel corso della giornata, il gruppo ha discusso delle loro esperienze di viaggio passate, condividendo momenti memorabili trascorsi insieme. "
                   "Sono stati menzionati luoghi particolarmente significativi, come la spiaggia e le escursioni in montagna, che hanno rievocato ricordi e aneddoti personali. "
                   "L'entusiasmo per il viaggio e la bellezza della natura sono stati temi ricorrenti.")
        messages = [
            {'username': 'utente1', 'type': 'text', 'content': "Guardate questa foto, è fantastica!", 'timestamp': datetime.now().timestamp(), 'caption': None},
            {'username': 'utente2', 'type': 'photo', 'content':"https://images.unsplash.com/photo-1507525428034-b723cf961d3e" , 'timestamp': datetime.now().timestamp(), 'caption': "Una vista panoramica del lago."},
            {'username': 'utente1', 'type': 'text', 'content': "Questo posto mi ricorda la mia infanzia.", 'timestamp': datetime.now().timestamp(), 'caption': None},
            {'username': 'utente3', 'type': 'text', 'content': "Wow, anche io ci sono stato l'anno scorso!", 'timestamp': datetime.now().timestamp(), 'caption': None},
            {'username': 'utente4', 'type': 'video', 'content': os.path.join(media_folder, "spiaggia_video.mp4"), 'timestamp': datetime.now().timestamp(), 'caption': "Ricordi dal viaggio estivo."},
            {'username': 'utente2', 'type': 'text', 'content': "Incredibile! Mi manca quel posto!", 'timestamp': datetime.now().timestamp(), 'caption': None},
            {'username': 'utente3', 'type': 'text', 'content': "Abbiamo catturato momenti davvero memorabili.", 'timestamp': datetime.now().timestamp(), 'caption': None},
            {'username': 'utente1', 'type': 'audio', 'content': os.path.join(media_folder, "spiaggia_audio.mp3"), 'timestamp': datetime.now().timestamp(), 'caption': None},
        ]
        return messages, context

    @staticmethod
    def uc3():
        context = ""
        messages = [
            {'username': 'utente1', 'type': 'text','content': "Avete letto l'ultimo articolo sulle tecnologie emergenti?",'timestamp': datetime.now().timestamp(), 'caption': None},
            {'username': 'utente2', 'type': 'photo', 'content': "https://imgcdn.agendadigitale.eu/wp-content/uploads/2024/03/27115746/image-32.png.webp",'timestamp': datetime.now().timestamp(), 'caption': "Diagramma sull'evoluzione delle leggi per l'AI"},
            {'username': 'utente3', 'type': 'text','content': "Sì, sembra che l'intelligenza artificiale stia davvero cambiando il mondo.",'timestamp': datetime.now().timestamp(), 'caption': None},
            {'username': 'utente4', 'type': 'text','content': "Secondo me, dobbiamo fare attenzione agli aspetti etici e normativi.",'timestamp': datetime.now().timestamp(), 'caption': None},
            {'username': 'utente1', 'type': 'text','content': "Concordo, ho attivato un filtro per seguire questi temi nella chat.",'timestamp': datetime.now().timestamp(), 'caption': None},
            {'username': 'utente2', 'type': 'audio', 'content': os.path.join(media_folder, "ai_discussion.mp3"),'timestamp': datetime.now().timestamp(), 'caption': "Discussione sulla normativa AI"},
            {'username': 'utente3', 'type': 'text', 'content': "Qualcuno ha già letto la proposta di legge?",'timestamp': datetime.now().timestamp(), 'caption': None},
            {'username': 'utente4', 'type': 'text','content': "Sì, penso sia un buon punto di partenza per una normativa più rigorosa.",'timestamp': datetime.now().timestamp(), 'caption': None},
        ]
        return messages, context

    @staticmethod
    def uc4():
        context = ("Nella giornata precedente, il gruppo ha affrontato diverse tematiche di rilievo, "
                   "concentrandosi su decisioni strategiche e discussioni approfondite. "
                   "Sono state condivise opinioni contrastanti e punti di vista su questioni fondamentali, "
                   "con l'obiettivo di raggiungere una visione comune. "
                   "A conclusione, gli utenti hanno apprezzato il confronto costruttivo e hanno manifestato l'intenzione di proseguire il dialogo per consolidare le decisioni prese")
        messages = [
            {'username': 'utente1', 'type': 'text', 'content': "È stato un giorno intenso, tante discussioni importanti.", 'timestamp': datetime.now().timestamp(), 'caption': None},
            {'username': 'utente2', 'type': 'text', 'content': "Assolutamente. Abbiamo preso decisioni cruciali.", 'timestamp': datetime.now().timestamp(), 'caption': None},
            {'username': 'utente3', 'type': 'text', 'content': "Non vedo l'ora di vedere il riassunto di oggi.", 'timestamp': datetime.now().timestamp(), 'caption': None},
            {'username': 'utente1', 'type': 'photo', 'content': "https://images.pexels.com/photos/7120126/pexels-photo-7120126.jpeg", 'timestamp': datetime.now().timestamp(), 'caption': "Foto della discussione conclusiva."},
            {'username': 'utente4', 'type': 'text', 'content': "Spero che il riassunto catturi tutto quanto.", 'timestamp': datetime.now().timestamp(), 'caption': None},
        ]
        return messages, context
