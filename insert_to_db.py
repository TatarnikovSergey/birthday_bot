import pandas as pd
import sqlite3

from parameters import FILE_PATH, SHEET_NAME

# Шаг 1: Чтение данных из Excel файла
excel_file = FILE_PATH
sheet_name = SHEET_NAME
data = pd.read_excel(excel_file, sheet_name=sheet_name)

# Преобразование столбцов с датами в нужный формат
if 'date_of_employment' in data.columns:
    data['date_of_employment'] = pd.to_datetime(data['date_of_employment']).dt.date.astype(str)

if 'date_of_birth' in data.columns:
    data['date_of_birth'] = pd.to_datetime(data['date_of_birth']).dt.date.astype(str)

# Шаг 2: Создание (или подключение к) SQLite базы данных
conn = sqlite3.connect('staff.db')  # Укажите имя вашей базы данных
cursor = conn.cursor()

# Шаг 3: Создание таблицы (если она еще не существует)
cursor.execute('''
CREATE TABLE IF NOT EXISTS staff (
    id INTEGER PRIMARY KEY,
    name TEXT,
    tabel_num INTEGER,
    position TEXT,
    date_of_employment TEXT,
    date_of_birth TEXT,    
    phone_number TEXT)
''')

# Шаг 4: Заполнение таблицы данными из DataFrame
data.to_sql('staff', conn, if_exists='append', index=False)

# Шаг 5: Закрытие соединения с базой данных
conn.commit()
conn.close()

print("Данные успешно загружены в базу данных!")


