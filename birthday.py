import os
import sqlite3
import threading
import time
from datetime import datetime, timedelta

import telebot
from dotenv import load_dotenv
from telebot import types

load_dotenv()

ADMIN_CHAT = os.getenv('ADMIN_CHAT_ID')
API_TOKEN = os.getenv('T_TOKEN')
bot = telebot.TeleBot(API_TOKEN)
current_time = datetime.now()  # .time()

stacked = []
waiting_users = []

# создаем клавиатуру
keyboard = types.InlineKeyboardMarkup()
# создаем кнопки, в скобочках первое - сообщение внутри кнопки,
# второе - текст по которому мы поймем, что именно эта кнопка была нажата (в телеграме этого не будет видно)
button1 = types.InlineKeyboardButton("Зарегистрировать", callback_data="yes")
button2 = types.InlineKeyboardButton("Отказать", callback_data="no")
# добавляем кнопки в клавиатуру
keyboard.add(button1, button2)


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
    # save_chat_id(chat_id, full_name)
    bot.send_message(chat_id=chat_id,
                     text=f'Приветствую Вас {full_name}. '
                          f'Этот Бот будет напоминать о дне рождения '
                          f'сотрудника за 3 дня!')
    bot.send_message(ADMIN_CHAT,
                     f'Зарегистрировать пользователя {full_name}?',
                     reply_markup=keyboard)
    waiting_users.append((chat_id, full_name))
    print(waiting_users)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    # Если кнопка "Зарегистрировать" была нажата
    if call.data == 'yes':
        try:
            chat_id, full_name = waiting_users.pop(0)  # !!!!!!!!!!!!!
            save_chat_id(chat_id, full_name)
            bot.send_message(chat_id=chat_id,
                             text=f'Вы зарегистрированы как {full_name}. '
                                  f'Бот напомнит Вам о дне рождения '
                                  f'сотрудника за 3 дня!')
            bot.send_message(ADMIN_CHAT,
                             f'Пользователь {full_name} зарегистрирован!')
        except Exception as e:
            bot.send_message(ADMIN_CHAT,
                             f'Ошибка {e}!!!')
    # Если кнопка "Отказать" была нажата
    elif call.data == 'no':
        try:
            chat_id, full_name = waiting_users.pop(0)  # !!!!!!!!!!!!!
            bot.send_message(chat_id=chat_id,
                             text=f'Вам отказано в регистрации как {full_name}, '
                                  f'поскольку Вы не являетесь сотрудником.')
            # bot.send_message(ADMIN_CHAT, f'Пользователь {full_name} отказался зарегистрироваться!')
        except Exception as e:
            bot.send_message(ADMIN_CHAT,
                             f'Ошибка {e}!!!')

    # Удаляем callback_query, чтобы не повторялась
    bot.answer_callback_query(callback_query_id=call.id)

    print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1')


def check_birthdays():
    """Проверяем дни рождения на следующие 3 дня"""
    today = datetime.now()
    # stacked = []

    # Подключаемся к базе данных
    con = sqlite3.connect('staff.db')
    cur = con.cursor()

    # Проверяем дни рождения на следующие 3 дня
    for days_ahead in range(1, 23):  # 1, 2 и 3 дня вперед
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
                    f'{day_to_filter}.{month_to_filter} день рождения '
                    f'сотрудника - {row[0]}!',
                    f'Ему исполнится {datetime.now().year - int(row[2][:4])}!')
                stacked.append(' '.join(birth))  # Объединяем строки в одну

    con.close()  # Закрываем соединение с БД


def send_message(bot, message):
    # Получаем всех пользователей для отправки сообщений
    con = sqlite3.connect('staff.db')
    cur = con.cursor()
    cur.execute('SELECT chat_id FROM users')
    user_ids = cur.fetchall()
    if current_time.weekday() == 2 and current_time.hour == 19:
        bot.send_message(ADMIN_CHAT, f'Кол-во зарегистрированных пользователей'
                                     f' - {len(user_ids)}')
    con.close()

    # Отправляем сообщения
    if stacked:  # Если есть сообщения для отправки
        for chat_id in user_ids:
            # print(chat_id, "-------", chat_id[0])
            chat_id = chat_id[0]  # Извлекаем chat_id из кортежа
            for message in stacked:
                try:
                    bot.send_message(chat_id=chat_id, text=message)
                    print(chat_id)
                    time.sleep(1)  # Задержка между отправкой сообщений
                except Exception as e:
                    bot.send_message(
                        ADMIN_CHAT,
                        f"Произошла ошибка: {e} "
                        f"при отправке сообщения в чат {chat_id}")
                    print(
                        f"Не удалось отправить сообщение "
                        f"пользователю {chat_id}: {e}")


def main():
    # Запускаем бота в отдельном потоке

    threading.Thread(target=bot.polling).start()

    while True:

        try:
            check_birthdays()
            # current_time = datetime.now()#.time()

            # if current_time.strftime('%H:%M') == '19:01':
            if 11 <= current_time.hour <= 14 \
                    and current_time.weekday() not in (5, 6):
                # print(current_time)
                send_message(bot, stacked)  # Отправляем сообщения
                stacked.clear()  # Очищаем стек сообщений
                time.sleep(86000)  # Ждем +-24 часа перед следующей проверкой
        except Exception as e:
            bot.send_message(ADMIN_CHAT, f"Произошла ошибка: {e}")
            print(f"Произошла ошибка: {e}")
            time.sleep(60)  # Ждем 1 минуту перед повторной попыткой


if __name__ == "__main__":
    main()
