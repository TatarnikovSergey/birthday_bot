import sqlite3


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
