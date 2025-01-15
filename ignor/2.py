import sqlite3
from datetime import datetime, timedelta
from pyrogram import Client
import time

api_id = 20144058
api_hash = '438ee2de12ff65b320453dda15c4a37d'
# Создаём программный клиент, передаём в него
# имя сессии и данные для аутентификации в Client API
app = Client('my_session', api_id=api_id, api_hash=api_hash)

# Вычисляем дату 214 дней назад
date = datetime.now() - timedelta(days=198)

# Форматируем текущую дату
current_date = date.strftime("%d.%m")
day_to_filter = date.strftime("%d")
month_to_filter = date.strftime("%m")

stacked = []

# Подключаемся к базе данных
con = sqlite3.connect('../staff.db')
cur = con.cursor()

# Выполняем параметризованный SQL-запрос
result = cur.execute('''
    SELECT name, phone_number, date_of_birth 
    FROM staff
    WHERE strftime('%d', date_of_birth) = ?
    AND strftime('%m', date_of_birth) = ?;
''', (day_to_filter, month_to_filter))

# Проверяем, есть ли результаты
rows = result.fetchall()  # Получаем все строки результата
if rows:  # Если есть строки
    for row in rows:
        birth = (
            f'{day_to_filter}.{month_to_filter} день рождения сотрудника - ',
            f'{row[0]}!',
            f'Ему исполнится {datetime.now().year - int(row[2][:4])}!')
        stacked.append(' '.join(birth))  # Объединяем строки в одну

con.close()  # Закрываем соединение с БД

# Запускаем клиента Pyrogram
app.start()

# Отправляем сообщения
for message in stacked:
    app.send_message('me', message)
    time.sleep(1)  # Задержка между отправкой сообщений

app.stop()  # Останавливаем клиента

# Выводим текущую дату
print(current_date)

