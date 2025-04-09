import sqlite3


def db_write(request, params, many=True):
    """Сохраняем данные в базу данных."""
    try:
        con = sqlite3.connect('staff.db')
        cur = con.cursor()
        if many:
            cur.executemany(request, params)
        else:
            cur.execute(request, params)
        con.commit()
        con.close()
    except sqlite3.Error as e:
        return f'Ошибка сохранения данных: {e}'
    except Exception as e:
        return f'Неожиданная ошибка сохранения данных: {e}'


def db_read(request, params=None):
    """Читаем данные из базы данных."""
    try:
        con = sqlite3.connect('staff.db')
        cur = con.cursor()
        if params is not None:
            cur.execute(request, params)
        else:
            cur.execute(request)
        rows = cur.fetchall()
        con.close()
        return rows
    except sqlite3.Error as e:
        return f'Ошибка чтения данных: {e}'
    except Exception as e:
        return f'Неожиданная ошибка чтения данных: {e}'


def save_user(chat_id, full_name):
    """Сохраняем пользователя в базу данных"""
    try:
        db_write('''
                INSERT OR IGNORE INTO users (chat_id, full_name) VALUES (?, ?);
    ''', (chat_id, full_name), many=False)
    except Exception as e:
        return f'Ошибка добавления пользователя: {e}'
