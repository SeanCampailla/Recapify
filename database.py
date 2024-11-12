from sqlalchemy import create_engine, Column, Integer, String, Text, Date, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date
import json


# Definisce il modello di base per SQLAlchemy
Base = declarative_base()

# Tabella per memorizzare i messaggi
class Message(Base):
    __tablename__ = 'messages'
    message_id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer)  # Identificatore della chat
    username = Column(String)  # Nome utente
    message_type = Column(String)  # Tipo di messaggio
    content = Column(Text)  # Contenuto del messaggio
    timestamp = Column(DateTime, default=datetime.now)  # Data e ora del messaggio
    caption = Column(String) # caption


# Tabella per memorizzare le preferenze delle chat
class ChatPreference(Base):
    __tablename__ = 'chat_preferences'
    chat_id = Column(Integer, primary_key=True)  # Identificatore della chat
    auto_summary = Column(Boolean, default=True)  # Auto-riassunto attivo/disattivo
    language = Column(String)  # Lingua preferita
    filter = Column(String)  # Filtro
    summary_length = Column(String)  # Lunghezza del riassunto


# Tabella per memorizzare i riassunti giornalieri
class Summary(Base):
    __tablename__ = 'summaries'
    summary_id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, ForeignKey('messages.chat_id'), index=True)  # Identificatore della chat, correlato a messages
    summary_content = Column(Text)  # Contenuto del riassunto
    summary_date = Column(Date, default=date.today)  # Data del riassunto


# Crea il motore SQLite (database salvato in un file chiamato 'chatbot.db')
engine = create_engine('sqlite:///chatbot.db')

# Crea una sessione per interagire con il database
Session = sessionmaker(bind=engine)
session = Session()

# Funzione per creare tutte le tabelle
def create_tables():
    Base.metadata.create_all(engine)

# Funzione per salvare un messaggio
def save_messages(chat_id, username, content, message_type="text", timestamp=None, caption=None):
    """Salva un messaggio nel database con l'ordine dei campi simile alla cache."""
    new_message = Message(
        chat_id=chat_id,
        username=username,
        message_type=message_type,
        content=content,
        timestamp=timestamp,
        caption=caption
    )
    with Session() as session:
        session.add(new_message)
        session.commit()
    print(f"Messaggio salvato: chat_id={chat_id}, username={username}, content={content}, type={message_type}")


# Funzione per recuperare i messaggi di una chat
def get_messages(chat_id):
    """Recupera i messaggi dal database nel formato della cache."""
    messages = session.query(Message).filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
    return [{'username': msg.username, 'type': msg.message_type, 'content': msg.content} for msg in messages]


# Funzione per salvare le preferenze di una chat
def save_chat_preferences(chat_id, auto_summary, language, filter, summary_length):
    # Controlla se esistono già preferenze per questa chat
    preference = session.query(ChatPreference).get(chat_id)

    if preference:
        # Aggiorna le preferenze esistenti
        preference.auto_summary = auto_summary
        preference.language = language
        preference.filter = filter
        preference.summary_length = summary_length
    else:
        # Crea nuove preferenze
        new_preference = ChatPreference(
            chat_id=chat_id,
            auto_summary=auto_summary,
            language=language,
            filter=filter,
            summary_length=summary_length)
        session.add(new_preference)

    session.commit()


# Funzione per recuperare le preferenze di una chat
def get_chat_preferences(chat_id):
    preference = session.query(ChatPreference).get(chat_id)
    if preference:
        return {
            'Auto-Riassunto': preference.auto_summary,
            'Lingua': preference.language,
            'Filtro': preference.filter,
            'Lunghezza Riassunto': preference.summary_length
        }
    return None

# Funzione per aggiungere un riassunto giornaliero
def add_summary(chat_id, summary_content):
    #Aggiunge un nuovo riassunto giornaliero per una chat.
    new_summary = Summary(chat_id=chat_id, summary_content=summary_content, summary_date=date.today())
    session.add(new_summary)
    session.commit()

# Funzione per recuperare un riassunto giornaliero per una specifica chat e data
def get_summary(chat_id, summary_date):
    #Recupera il riassunto di una chat per una data specifica.
    summary = session.query(Summary).filter_by(chat_id=chat_id, summary_date=summary_date).first()
    return summary.summary_content if summary else None


