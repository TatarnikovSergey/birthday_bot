import os
import sqlite3
import threading
import time
from datetime import datetime, timedelta

import telebot
from dotenv import load_dotenv

load_dotenv()


API_TOKEN = os.getenv('T_TOKEN')
bot = telebot.TeleBot(API_TOKEN)


def save_chat_id(chat_id, full_name):
    """Сохраняем chat_id в базу данных"""
    con = sqlite3.connect('staff.db')
    cur = con.cursor()
    cur.execute('''
            INSERT OR IGNORE INTO users (chat_id, full_name) VALUES (?, ?);
        ''', (chat_id, full_name))
    con.commit()
    con.close()


@bot.message_handler(commands=['start'])
def say_hi(message):
    """Получаем id чата и сохраняем его в базе данных"""
    chat_id = message.chat.id
    full_name = message.from_user.full_name
    save_chat_id(chat_id, full_name)
    bot.send_message(chat_id=chat_id,
                     text=f'Приветствую Вас {full_name}. '
                          f'Бот напомнит о дне рождения сотрудника за 3 дня!')


def check_birthdays():
    """Проверяем дни рождения на следующие 3 дня"""
    today = datetime.now()
    stacked = []

    # Подключаемся к базе данных
    con = sqlite3.connect('staff.db')
    cur = con.cursor()

    # Проверяем дни рождения на следующие 3 дня
    for days_ahead in range(1, 34):  # 1, 2 и 3 дня вперед
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

    # Получаем всех пользователей для отправки сообщений
    con = sqlite3.connect('staff.db')
    cur = con.cursor()
    cur.execute('SELECT chat_id FROM users')
    user_ids = cur.fetchall()
    con.close()

    # Отправляем сообщения
    if stacked:  # Если есть сообщения для отправки
        for chat_id in user_ids:
            # print(chat_id, "-------", chat_id[0])
            chat_id = chat_id[0]  # Извлекаем chat_id из кортежа
            for message in stacked:
                try:
                    bot.send_message(chat_id=chat_id, text=message)
                    time.sleep(1)  # Задержка между отправкой сообщений
                except Exception as e:
                    print(
                        f"Не удалось отправить сообщение пользователю {chat_id}: {e}")


def main():
    # Запускаем бота в отдельном потоке

    threading.Thread(target=bot.polling).start()

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
