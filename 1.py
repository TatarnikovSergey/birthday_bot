import pandas as pd
import sqlite3

# Шаг 1: Чтение данных из Excel файла
excel_file = 'ваш_файл.xlsx'  # Укажите путь к вашему Excel файлу
sheet_name = 'Лист1'  # Укажите имя листа, если необходимо
data = pd.read_excel(excel_file, sheet_name=sheet_name)

# Шаг 2: Создание (или подключение к) SQLite базы данных
conn = sqlite3.connect('ваша_база_данных.db')  # Укажите имя вашей базы данных
cursor = conn.cursor()

# Шаг 3: Создание таблицы (если она еще не существует)
# Предположим, что у вас есть колонки 'id', 'name', 'age' в Excel
cursor.execute('''
CREATE TABLE IF NOT EXISTS ваша_таблица (
    id INTEGER PRIMARY KEY,
    name TEXT,
    age INTEGER
)
''')

# Шаг 4: Заполнение таблицы данными из DataFrame
data.to_sql('ваша_таблица', conn, if_exists='append', index=False)

# Шаг 5: Закрытие соединения с базой данных
conn.commit()
conn.close()

print("Данные успешно загружены в базу данных!")

