import threading
from sqlalchemy import Column, String, BigInteger
from tg_bot.modules.sql import BASE, SESSION

class LoggerSettings(BASE):
    __tablename__ = "logger_settings"
    chat_id = Column(BigInteger, primary_key=True)
    chat_name = Column(String(255)) # Just for your reference in the DB

    def __init__(self, chat_id, chat_name):
        self.chat_id = chat_id
        self.chat_name = chat_name

# Create the table
LoggerSettings.__table__.create(checkfirst=True)

INSERTION_LOCK = threading.RLock()

def enable_logging(chat_id, chat_name):
    with INSERTION_LOCK:
        curr = SESSION.query(LoggerSettings).get(chat_id)
        if not curr:
            curr = LoggerSettings(chat_id, chat_name)
            SESSION.add(curr)
            SESSION.commit()

def disable_logging(chat_id):
    with INSERTION_LOCK:
        curr = SESSION.query(LoggerSettings).get(chat_id)
        if curr:
            SESSION.delete(curr)
            SESSION.commit()

def is_logging_enabled(chat_id):
    try:
        return SESSION.query(LoggerSettings).get(chat_id) is not None
    finally:
        SESSION.close()

def get_all_logged_chats():
    try:
        return SESSION.query(LoggerSettings).all()
    finally:
        SESSION.close()