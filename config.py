import os

class Config:
    API_ID = os.getenv("API_ID", "default_api_id")
    API_HASH = os.getenv("API_HASH", "default_api_hash")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "default_bot_token")
    NGROK_URL = os.getenv("NGROK_URL", "https://default.ngrok.url")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "default_openai_api_key")
