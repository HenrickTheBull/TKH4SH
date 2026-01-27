import threading

from sqlalchemy import Column, String

from tg_bot.modules.sql import BASE, SESSION


class PipeUsers(BASE):
    __tablename__ = "pipe"
    user_id = Column(String(14), primary_key=True)
    handle = Column(String(255))

    def __init__(self, user_id, handle):
        self.user_id = user_id
        self.handle = handle


PipeUsers.__table__.create(checkfirst=True)

INSERTION_LOCK = threading.RLock()


def set_handle(user_id, handle):
    with INSERTION_LOCK:
        user = SESSION.query(PipeUsers).get(str(user_id))
        if not user:
            user = PipeUsers(str(user_id), str(handle))
        else:
            user.handle = str(handle)

        SESSION.add(user)
        SESSION.commit()


def get_handle(user_id):
    user = SESSION.query(PipeUsers).get(str(user_id))
    rep = ""
    if user:
        rep = str(user.handle)

    SESSION.close()
    return rep
