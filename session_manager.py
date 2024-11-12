#session_manager.py
from user_session import UserSession

class SessionManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance.sessions = {}
        return cls._instance

    async def get_session(self, chat_id):
        if chat_id not in self.sessions:
            self.sessions[chat_id] = await UserSession.create(chat_id) 
        return self.sessions[chat_id]

    def clear_all_sessions(self):
        self.sessions.clear()
