import sqlite3
conn = sqlite3.connect('staff.db')  # Укажите имя вашей базы данных
cursor = conn.cursor()

# Шаг 3: Создание таблицы (если она еще не существует)
# Предположим, что у вас есть колонки 'id', 'name', 'age' в Excel
cursor.execute('''CREATE TABLE users (
    chat_id INTEGER PRIMARY KEY
);
''')

conn.commit()
conn.close()