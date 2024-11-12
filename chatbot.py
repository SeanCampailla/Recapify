
# chatbot.py

import asyncio
import logging
from datetime import datetime, timedelta

from config import Config
from localization import LANGUAGES
from session_manager import SessionManager
from telethon import TelegramClient, events, Button


# Configurazione del logger
logger = logging.getLogger("bot")
logger.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.INFO)

# Da sistemare l'inoltro delle preference appena cambiate
# Da sistemare l'ui per preference


class TelegramBot:
    def __init__(self):
        self.api_id = Config.API_ID
        self.api_hash = Config.API_HASH
        self.bot_token = Config.BOT_TOKEN
        self.client = TelegramClient('anon', api_id=self.api_id, api_hash=self.api_hash)
        self.session_manager = SessionManager()

        # Gestori Eventi
        self.client.add_event_handler(self.handle_start_command, events.NewMessage(pattern='/start'))
        self.client.add_event_handler(self.handle_help_command, events.NewMessage(pattern='/help'))
        self.client.add_event_handler(self.handle_text_message, events.NewMessage(incoming=True))

        # Gestore Pulsanti
        self.client.add_event_handler(self.handle_callback_query, events.CallbackQuery)

        # Avvio del task per il riassunto giornaliero
        asyncio.create_task(self.daily_summary_timer())

        # Mappatura delle preferenze
        self.preference_mapping = {
            'yes_auto': ("Auto-Riassunto", True),
            'no_auto': ("Auto-Riassunto", False),
            'it': ("Lingua", "it"),
            'en': ("Lingua", "en"),
            'fr': ("Lingua", "fr"),
            'breve': ("Lunghezza Riassunto", 'breve'),
            'medio': ("Lunghezza Riassunto", 'medio'),
            'lungo': ("Lunghezza Riassunto", 'lungo'),
        }

        # Struttura del menu (usa chiavi per la localizzazione)
        self.menu_structure = {
            'main_menu': {
                'text_key': 'main_menu_text',
                'buttons': [('summarize', 'summarize'), ('preferences', 'preferences'), ('settings', 'options_menu')],
                'previous': None
            },
            'options_menu': {
                'text_key': 'settings_menu_text',
                'buttons': [('language', 'language_menu'), ('daily_summary', 'auto_summary_menu'),
                            ('filter', 'filters'), ('summary_length', 'summary_length_menu')],
                'previous': 'main_menu'
            },
            'language_menu': {
                'text_key': 'language_menu_text',
                'buttons': [('Italiano', 'it'), ('Inglese', 'en'), ('Francese', 'fr')],
                'previous': 'options_menu'
            },
            'summary_length_menu': {
                'text_key': 'summary_length_menu_text',
                'buttons': [('breve', 'breve'), ('medio', 'medio'), ('lungo', 'lungo')],
                'previous': 'options_menu'
            },
            'auto_summary_menu': {
                'text_key': 'auto_summary_menu_text',
                'buttons': [('activate', 'yes_auto'), ('deactivate', 'no_auto')],
                'previous': 'options_menu'
            },
            'summary_settings_menu': {
                'text_key': 'summary_settings_menu_text',
                'buttons': [('max_messages', 'max_messages_menu'), ('max_time', 'max_time_menu')],
                'previous': 'options_menu'
            }
        }

    async def start_bot(self):
        await self.client.start(bot_token=self.bot_token)
        logger.info("Bot avviato con successo.")
        await self.client.run_until_disconnected()

    # Handler per la gestione dei comandi
    async def handle_start_command(self, event):
        chat_id = event.chat_id if hasattr(event, 'chat_id') else event.sender_id
        user_session = await self.session_manager.get_session(chat_id)
        language = await user_session.get_preference("Lingua") or 'it'
        localization = LANGUAGES.get(language, LANGUAGES['it'])
        welcome_text = localization.get('main_menu_text', "Benvenuto! Scegli un'opzione dal menu:")
        # Risponde al comando /start con il menu principale e un messaggio di benvenuto.
        await self.show_menu(event, 'main_menu', welcome_text)

    async def handle_summarize_command(self, event):
        chat_id = event.chat_id if hasattr(event, 'chat_id') else event.sender_id
        if isinstance(event, events.CallbackQuery.Event):
            await event.answer()

        chat_id = event.chat_id if hasattr(event, 'chat_id') else event.sender_id
        user_session = await self.session_manager.get_session(chat_id)
        language = await user_session.get_preference("Lingua") or 'it'
        localization = LANGUAGES.get(language, LANGUAGES['it'])

        await event.respond(localization.get('processing_summary'))
        summary = await user_session.get_summary()
        await event.respond(summary)

    async def handle_preferences_command(self, event):
        chat_id = event.chat_id if hasattr(event, 'chat_id') else event.sender_id
        user_session = await self.session_manager.get_session(chat_id)

        # Recupera le preferenze dell'utente
        preferences = {
            "Auto-Riassunto": await user_session.get_preference("Auto-Riassunto"),
            "Lingua": await user_session.get_preference("Lingua"),
            "Filtro": await user_session.get_preference("Filtro"),
            "Lunghezza Riassunto": await user_session.get_preference("Lunghezza Riassunto"),
        }

        # Formatta le preferenze per la visualizzazione
        preferences_text = "\n".join([f"{key}: {value}" for key, value in preferences.items()])

        # Localizza il messaggio e invia le preferenze all'utente
        language = preferences["Lingua"] or 'it'
        localization = LANGUAGES.get(language, LANGUAGES['it'])
        preferences_header = localization.get('preferences_header', "Preferenze attuali:")

        await event.respond(f"{preferences_header}\n{preferences_text}")

    async def handle_help_command(self, event):
        chat_id = event.chat_id if hasattr(event, 'chat_id') else event.sender_id
        user_session = await self.session_manager.get_session(chat_id)
        language = await user_session.get_preference("Lingua") or 'it'
        localization = LANGUAGES.get(language, LANGUAGES['it'])
        help_text = localization.get('help_text', "Ecco la lista dei comandi:")
        await self.show_menu(event, 'main_menu', help_text)

    async def handle_text_message(self, event):
        # Gestisce i messaggi di testo per impostare il filtro solo se `pending_filters` è attivo per quella chat e utente specifici.
        chat_id = event.chat_id if hasattr(event, 'chat_id') else event.sender_id
        user_id = event.sender_id
        user_session = await self.session_manager.get_session(chat_id)
        language = await user_session.get_preference("Lingua") or 'it'
        localization = LANGUAGES.get(language, LANGUAGES['it'])

        user = await self.client.get_entity(user_id)
        if await user_session.is_pending_filter(user.username):
            if event.text:
                await user_session.update_preference("Filtro", event.text)
                await event.respond(
                    localization.get('confirmation_update').format(key=localization.get('filter'), value=event.text))
                await user_session.remove_pending_filter(user.username)
                return
            else:
                await event.respond(localization.get('error_invalid_format'))
        else:
            return

    # Gestione Pulsanti ed interfaccia utente
    async def show_menu(self, event, menu_name, custom_text=None):
        # Mostra il menu specificato con i pulsanti inline e un testo opzionale.
        menu = self.menu_structure.get(menu_name)
        if not menu:
            await event.respond("Errore: menu non trovato.")
            return

        # Recupera la preferenza linguistica dell'utente
        chat_id = event.chat_id if hasattr(event, 'chat_id') else event.sender_id
        user_session = await self.session_manager.get_session(chat_id)
        language = await user_session.get_preference("Lingua") or 'it'
        localization = LANGUAGES.get(language, LANGUAGES['it'])

        # Usa custom_text se fornito, altrimenti usa il testo predefinito del menu
        text = custom_text if custom_text else localization.get(menu['text_key'], menu['text_key'])

        # Crea i pulsanti principali del menu con etichette localizzate
        buttons = []
        for label_key, data in menu['buttons']:
            label = localization.get(label_key, label_key)
            buttons.append(Button.inline(label, data.encode('utf-8')))
        buttons = [buttons]  # wrap in another list to make it a list of lists

        # Aggiungi il pulsante "Indietro" se esiste un menu precedente
        if menu['previous']:
            back_label = localization.get('back', 'Indietro')
            buttons.append([Button.inline(back_label, menu['previous'].encode('utf-8'))])

        # Invia o modifica il messaggio per mostrare il menu
        if isinstance(event, events.NewMessage.Event):
            await event.respond(text, buttons=buttons)
        elif isinstance(event, events.CallbackQuery.Event):
            await event.edit(text, buttons=buttons)

    async def handle_callback_query(self, event):
        # Gestisce la navigazione nei menu e l'aggiornamento delle preferenze tramite pulsanti inline.
        data = event.data.decode('utf-8')
        chat_id = event.chat_id if hasattr(event, 'chat_id') else event.sender_id
        user_id = event.sender_id
        user_session = await self.session_manager.get_session(chat_id)
        language = await user_session.get_preference("Lingua") or 'it'
        localization = LANGUAGES.get(language, LANGUAGES['it'])

        if data in self.menu_structure:
            await self.show_menu(event, data)

        elif data in self.preference_mapping:
            key, value = self.preference_mapping[data]
            await user_session.update_preference(key, value)
            confirmation_text = localization.get('confirmation_update', "Preferenza '{key}' aggiornata a '{value}'.")
            await event.answer(
                confirmation_text.format(key=localization.get(key.lower(), key), value=localization.get(value, value)))
            await self.show_menu(event, 'main_menu')

        elif data == 'summarize':
            await self.handle_summarize_command(event)

        elif data == 'preferences':
            await self.handle_preferences_command(event)

        elif data == 'filters':
            await event.respond(localization.get('set_filter_placeholder')) #da controllare
            user = await self.client.get_entity(user_id)
            await user_session.add_pending_filter(user.username)

    async def daily_summary_timer(self):
        while True:
            now = datetime.now()
            next_run = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
            delay = (next_run - now).total_seconds()
            await asyncio.sleep(delay)

            await self.send_daily_summary_to_all()

    async def send_daily_summary_to_all(self):
        for chat_id in self.session_manager.sessions:
            session = await self.session_manager.get_session(chat_id)
            if await session.get_preference("Auto-Riassunto"):
                summary_content = await session.get_summary()
                await self.send_daily_summary(chat_id, summary_content)
                await session.daily_store()

    async def send_daily_summary(self, chat_id, summary_content):
        session = await self.session_manager.get_session(chat_id)
        language = await session.get_preference("Lingua") or 'it'
        localization = LANGUAGES.get(language, LANGUAGES['it'])
        summary_text = localization.get('daily_summary', "Riassunto giornaliero") +":\n"+summary_content
        await self.client.send_message(chat_id, summary_text)
        logging.info(f"Riassunto giornaliero inviato alla chat {chat_id}.")
