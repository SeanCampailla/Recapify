# webhook.py

import logging

import httpx
import requests
from config import Config
from models import Update
from pyngrok import ngrok
from quart import Quart, request, jsonify
from session_manager import SessionManager

app = Quart(__name__)

session_manager = SessionManager()

# Configurazione del logger
logger = logging.getLogger("webhook")
logger.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.INFO)


def set_webhook():
    public_url = ngrok.connect(8000, bind_tls=True).public_url
    webhook_url = f"{public_url}/webhook"
    # print(webhook_url)

    response = requests.post(
        f"https://api.telegram.org/bot{Config.BOT_TOKEN}/setWebhook",
        json={"url": webhook_url}
    )

    logger.info(f"Webhook_url: {webhook_url}")
    if response.status_code == 200:
        logger.info("Webhook impostato con successo.")
    else:
        logger.error(f"Errore durante l'impostazione del webhook: {response.text}")


@app.errorhandler(Exception)
async def handle_error(error):
    status_code = getattr(error, 'code', 500)
    error_message = {
        400: "Richiesta malformata",
        404: "Risorsa non trovata",
        500: "Errore interno del server"
    }.get(status_code, "Errore sconosciuto")

    logger.error(f"Errore {status_code}: {error}")
    return jsonify({"error": error_message}), status_code


@app.route('/webhook', methods=['POST'])
async def webhook():  # sistemare gestione creazione sessione utente
    try:
        data = await request.json
        update = Update(**data)

        if update.message:
            message = update.message
            chat_id = message.chat.id
            if message.from_user.username:
                username = message.from_user.username
            elif message.from_user.first_name or message.from_user.last_name:
                username = message.from_user.first_name + " " + message.from_user.last_name
            else:
                username = 'Sconosciuto'
            # Gestione del messaggio
            await process_message(message, username, chat_id)

        return '', 200
    except Exception as e:
        logger.error(f"Errore nel webhook: {e}")
        return '', 500


async def process_message(message, username, chat_id):
    # Ottieni la sessione dell'utente
    user_session = await session_manager.get_session(chat_id)
    media_fields = ['photo', 'video', 'document', 'audio', 'voice', 'animation', 'sticker', 'video_note']
    timestamp = message.date

    if message.caption is not None:
        caption = message.caption
    else:
        caption = ""

    # Gestione dei messaggi di testo
    if message.text and not message.text.startswith("/"):  # Ignora i comandi
        await user_session.add_message(username, 'text', message.text, timestamp, caption)
    else:
        # Gestione dei media
        for media_field in media_fields:
            media = getattr(message, media_field, None)
            if media:
                if isinstance(media, list):  # Gestione delle foto (lista di Media)
                    media = media[-1]  # Ottieni la risoluzione più alta

                # Gestion tipi sticker
                if media_field == 'sticker':
                    if media.is_animated:
                        media_field = 'video'
                # Gestione tipi documento
                if media_field == 'document':
                    if media.mime_type.startswith('image'):
                        media_field = 'photo'
                    elif media.mime_type.startswith('video'):
                        media_field = 'video'

                file_url = await get_file_url(media.file_id)
                if file_url:
                    await user_session.add_message(username, media_field, file_url, timestamp, caption)
                    # logger.info(f'Media {media_field} ricevuto da {username} (chat ID: {chat_id}): {file_url}')


async def get_file_url(file_id):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.telegram.org/bot{Config.BOT_TOKEN}/getFile?file_id={file_id}")
        if response.status_code == 200:
            file_info = response.json()
            if 'result' in file_info:
                file_path = file_info['result'].get('file_path')
                if file_path:
                    return f"https://api.telegram.org/file/bot{Config.BOT_TOKEN}/{file_path}"
                else:
                    logger.error("'file_path' non trovato nella risposta di Telegram.")
            else:
                logger.error("'result' non trovato nella risposta di Telegram.")
        else:
            logger.error(f"Errore durante il recupero del file da Telegram: {response.status_code} - {response.text}")
        return None
