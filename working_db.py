import os
import sqlite3

from dotenv import load_dotenv

from send_message import send_message

load_dotenv()

ADMIN_CHAT = os.getenv('ADMIN_CHAT_ID')


def db_write(request, var, many=True):
    """Сохраняем данные в базу данных."""
    con = sqlite3.connect('staff.db')
    cur = con.cursor()
    if many:
        cur.executemany(request, var)
    else:
        cur.execute(request, var)
    con.commit()
    con.close()


def db_read(request, var=None):
    """Читаем данные из базы данных."""
    con = sqlite3.connect('staff.db')
    cur = con.cursor()
    if var is not None:
        cur.execute(request, var)
    else:
        cur.execute(request)
    rows = cur.fetchall()
    con.close()
    return rows


def save_user(chat_id, full_name):
    """Сохраняем пользователя в базу данных"""
    try:
        db_write('''
    INSERT OR IGNORE INTO users (chat_id, full_name) VALUES (?, ?);
    ''', (chat_id, full_name), many=False)
    except Exception as e:
        send_message(ADMIN_CHAT, f'Ошибка добавления пользователя: {e}')
