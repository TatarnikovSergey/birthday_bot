import sqlite3
from datetime import datetime, timedelta
from pyrogram import Client
import time
import sys

api_id = 20144058
api_hash = '438ee2de12ff65b320453dda15c4a37d'
app = Client('my_session', api_id=api_id, api_hash=api_hash)

def check_birthdays():
    today = datetime.now()
    stacked = []

    # Подключаемся к базе данных
    con = sqlite3.connect('staff.db')
    cur = con.cursor()

    # Проверяем дни рождения на следующие 3 дня
    for days_ahead in range(1, 4):  # 1, 2 и 3 дня вперед
        date_to_check = today + timedelta(days=days_ahead)
        day_to_filter = date_to_check.strftime("%d")
        month_to_filter = date_to_check.strftime("%m")

        # Выполняем параметризованный SQL-запрос
        result = cur.execute('''
            SELECT name, phone_number, date_of_birth 
            FROM staff
            WHERE strftime('%d', date_of_birth) = ?
            AND strftime('%m', date_of_birth) = ?;
        ''', (day_to_filter, month_to_filter))

        # Получаем все строки результата
        rows = result.fetchall()
        if rows:  # Если есть строки
            for row in rows:
                birth = (
                    f'{day_to_filter}.{month_to_filter} день рождения сотрудника - ',
                    f'{row[0]}!',
                    f'Ему исполнится {datetime.now().year - int(row[2][:4])}!')
                stacked.append(' '.join(birth))  # Объединяем строки в одну

    con.close()  # Закрываем соединение с БД

    # Запускаем клиента Pyrogram
    # app.start()
    print(len(stacked))
    # Отправляем сообщения
    if stacked:  # Если есть сообщения для отправки
        for message in stacked:
            # app.send_message('me', message)
            print(message)  # Выводим отправленные сообщения на консоль
            stacked.pop()
            time.sleep(1)  # Задержка между отправкой сообщений

    # app.stop()  # Останавливаем клиента
    print(len(stacked))
def main():
    while True:
        try:
            check_birthdays()
            # Ждем 24 часа перед следующей проверкой
            time.sleep(86400)  # 86400 секунд = 24 часа
        except Exception as e:
            print(f"Произошла ошибка: {e}")
            time.sleep(60)  # Ждем 1 минуту перед повторной попыткой


if __name__ == "__main__":
    main()
