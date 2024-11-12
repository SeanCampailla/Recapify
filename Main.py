# app.py

import asyncio
import logging

import hypercorn.asyncio
from chatbot import TelegramBot
from database import create_tables
from hypercorn.config import Config as HypercornConfig
from webhook import app, set_webhook

# Configurazione del logger
logger = logging.getLogger("app")
logger.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.INFO)


async def start_servers():
    create_tables()

    hypercorn_config = HypercornConfig()
    hypercorn_config.bind = ["0.0.0.0:8000"]
    set_webhook()

    bot = TelegramBot()

    await asyncio.gather(
        bot.start_bot(),
        hypercorn.asyncio.serve(app, hypercorn_config)
    )

if __name__ == "__main__":
    asyncio.run(start_servers())

