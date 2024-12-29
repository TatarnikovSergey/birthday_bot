import sqlite3
from datetime import datetime, timedelta
import telebot
import time
import os




# Замените 'YOUR_BOT_TOKEN' на токен вашего бота Telegram
API_TOKEN = '7856229838:AAEvCPPNUZ78aBpNTxni5CBpdF6-X3pS9Ug'
bot = telebot.TeleBot(API_TOKEN)
chat_id = None

@bot.message_handler(content_types=['text'])
def say_hi(message):
    chat = message.chat
    chat_id = chat.id
    bot.send_message(chat_id=chat_id, text='Бот напомнит о дне рождения за 3 дня!')

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

    # Отправляем сообщения
    if stacked:  # Если есть сообщения для отправки
        for message in stacked:
            # Замените 'YOUR_CHAT_ID' на ваш chat_id или chat_id группы

            bot.send_message(chat_id=chat_id, text=message)
            time.sleep(1)  # Задержка между отправкой сообщений

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
