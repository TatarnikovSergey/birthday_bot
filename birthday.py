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
staff_data = {}
staff_edit_id = []
staff_edit_data = {}

# создаем клавиатуры
keyboard_start = types.InlineKeyboardMarkup()
keyboard_crud = types.InlineKeyboardMarkup()
keyboard_staff = types.InlineKeyboardMarkup()
# создаем кнопки
button1 = types.InlineKeyboardButton("Зарегистрировать", callback_data="yes")
button2 = types.InlineKeyboardButton("Отказать", callback_data="no")
button3 = types.InlineKeyboardButton("Добавить", callback_data="add")
button4 = types.InlineKeyboardButton("Изменить", callback_data="edit")
button5 = types.InlineKeyboardButton("Удалить", callback_data="delete")
button6 = types.InlineKeyboardButton("Список сотрудников", callback_data="list_staff")
button7 = types.InlineKeyboardButton("ФИО", callback_data="fio")
# button8 = types.InlineKeyboardButton("Табельный номер", callback_data="tub_num")
button9 = types.InlineKeyboardButton("Должность", callback_data="position")
# button10 = types.InlineKeyboardButton("Дата трудоустройства", callback_data="date")
button11 = types.InlineKeyboardButton("Номер телефона", callback_data="phone")
# button7 = types.InlineKeyboardButton("All users", callback_data="list_users")
# добавляем кнопки в клавиатуру
keyboard_start.add(button1, button2)
keyboard_crud.add(button3, button4, button5, button6)
keyboard_staff.add(button7, button9, button11)


def db_record(request, var, many=True):
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


def save_user(chat_id, full_name):
    """Сохраняем пользователя в базу данных"""
    try:
        db_record('''
    INSERT OR IGNORE INTO users (chat_id, full_name) VALUES (?, ?);
    ''', (chat_id, full_name))
    except Exception as e:
        bot.send_message(ADMIN_CHAT, f'Ошибка добавления пользователя: {e}')


@bot.message_handler(commands=['start'])
def say_hi(message):
    """Получаем данные нового пользователя."""
    chat_id = message.chat.id
    full_name = message.from_user.full_name
    bot.send_message(chat_id=chat_id,
                     text=f'Приветствую Вас {full_name}. '
                          f'Этот Бот будет напоминать о дне рождения '
                          f'сотрудника за 3 дня!')
    bot.send_message(ADMIN_CHAT,
                     f'Зарегистрировать пользователя {full_name}?',
                     reply_markup=keyboard_start)
    waiting_users.append((chat_id, full_name))
    print(waiting_users)


@bot.message_handler(commands=['crud'])
def crud_staff(message):
    """Отправляем кнопки CRUD."""
    bot.send_message(message.chat.id, "CRUD-операции с сотрудниками:",
                     reply_markup=keyboard_crud)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    """Обработка нажатий кнопок."""
    if call.data == 'yes':  # Если кнопка "Зарегистрировать" была нажата
        try:
            chat_id, full_name = waiting_users.pop(0)  # !!!!!!!!!!!!!
            save_user(chat_id, full_name)
            bot.send_message(chat_id,
                             f'Вы зарегистрированы как {full_name}. '
                             f'Бот напомнит Вам о дне рождения '
                             f'сотрудника за 3 дня!')
            bot.send_message(ADMIN_CHAT,
                             f'Пользователь {full_name} зарегистрирован!')
        except Exception as e:
            bot.send_message(ADMIN_CHAT, f'Ошибка {e}!!!')
    elif call.data == 'no':  # Если кнопка "Отказать" была нажата
        try:
            chat_id, full_name = waiting_users.pop(0)  # Достаем пользователя
            bot.send_message(chat_id,
                             f'Вам отказано в регистрации как {full_name}, '
                             f'поскольку Вы не являетесь сотрудником.')
        except Exception as e:
            bot.send_message(ADMIN_CHAT, f'Ошибка {e}!!!')
    elif call.data == 'add':
        bot.send_message(call.message.chat.id, "Добавление нового сотрудника:")
        staff_data[call.message.chat.id] = {}  # Инициализируем словарь для хранения данных
        bot.send_message(call.message.chat.id, "Введите ФИО сотрудника:")
        bot.register_next_step_handler(call.message, get_name)
    elif call.data == 'delete':
        bot.send_message(call.message.chat.id, "Введите имя сотрудника для удаления:")
        bot.register_next_step_handler(call.message, del_staff)
    elif call.data == 'list_staff':
        get_list_staff(call)
    elif call.data == 'edit':
        bot.send_message(call.message.chat.id, "Введите ФИО сотрудника для редактирования:")
        staff_data[call.message.chat.id] = {}
        bot.register_next_step_handler(call.message, edit_staff)






    # Удаляем callback_query, чтобы не повторялась
    bot.answer_callback_query(callback_query_id=call.id)


def edit_staff(message):
    try:
        staff_name = message.text.strip()
        rows = db_read('''
            SELECT * FROM staff WHERE name = ?;
        ''', (staff_name,))
        print(rows)
        if not rows:
            bot.send_message(message.chat.id, "Сотрудник не найден.")
            return
        staff_edit_id = rows[0][0]
        staff_edit_data[message.chat.id] = {
            'edit_id': staff_edit_id,
            'name': rows[0][1],
            'position': rows[0][3],
            'phone_number': rows[0][6]
        }
        staff_data = {
            'ФИО': rows[0][1],
            'Должность': rows[0][3],
            'Номер телефона': rows[0][6]
        }
        bot.send_message(message.chat.id,
                         f"Что вы хотите изменить?:\n{staff_data}\n"
                         "Введите номер поля для редактирования:\n"
                         "1. ФИО\n2. Должность\n3. Номер телефона")
        bot.register_next_step_handler(message, select_field)
    except Exception as e:
        bot.send_message(message.chat.id,
                         f"Произошла ошибка при обновлении: {e}")


def select_field(message):
    field_mapping = {
        '1': ('ФИО', 'name'),
        '2': ('Должность', 'position'),
        '3': ('Номер телефона', 'phone_number')
    }
    field_number = message.text.strip()
    field_info = field_mapping.get(field_number)
    if field_info:
        field_label, field_name = field_info
        bot.send_message(message.chat.id, f"Введите новое значение для {field_label}:")
        bot.register_next_step_handler(message, update_field, field_name)
    else:
        bot.send_message(message.chat.id, "Неверный номер поля.")
        bot.register_next_step_handler(message, select_field)


def update_field(message, field_name):
    new_value = message.text  # Получаем новое значение от пользователя
    staff_edit_id = staff_edit_data[message.chat.id]['edit_id']  # ID редактируемого сотрудника
    try:
        db_record(f'''
            UPDATE staff SET {field_name} = ? WHERE id = ?;
        ''', (new_value, staff_edit_id), many=False)
        bot.send_message(message.chat.id, "Данные успешно обновлены.")
    except Exception as e:
        bot.send_message(message.chat.id,
                         f"Произошла ошибка при обновлении: {e}")


def get_list_staff(call):
    staff_list = db_read('''
            SELECT name, position, phone_number
            FROM staff
            ORDER BY name ASC;
            ''')

    # Форматируем список сотрудников в строку
    if staff_list:
        staff_message = "Список сотрудников:\n"
        for staff in staff_list:
            fio = staff[0].split()
            short_fio = f"{fio[0]} {fio[1][0]}." \
                        f"{fio[2][0] if len(fio) >= 3 else None}."
            staff_message += f'{short_fio}\n {staff[2]}\n --\n'
    else:
        staff_message = "Список сотрудников пуст."

        # Разбиваем сообщение на части, если оно слишком длинное
    max_length = 4096
    if len(staff_message) > max_length:
        for i in range(0, len(staff_message), max_length):
            bot.send_message(call.message.chat.id,
                             staff_message[i:i + max_length])
    else:
        # Отправляем сообщение с полным списком сотрудников
        bot.send_message(call.message.chat.id, staff_message)


def get_name(message):
    name = message.text.strip()
    bot.send_message(message.chat.id, name)
    if len(name.split()) <= 1 or any(i.isdigit() for i in name):
        bot.send_message(message.chat.id, "Введите корректное ФИО:")
        bot.register_next_step_handler(message, get_name)
        return
    staff_data[message.chat.id]['name'] = name
    bot.send_message(message.chat.id, "Введите табельный номер:")
    bot.register_next_step_handler(message, get_tabel_num)


def get_tabel_num(message):
    if not message.text.isdigit():
        bot.send_message(message.chat.id,
                         "Введите корректный табельный номер (число):")
        bot.register_next_step_handler(message, get_tabel_num)
        return
    staff_data[message.chat.id]['tabel_num'] = message.text
    bot.send_message(message.chat.id, "Введите должность:")
    bot.register_next_step_handler(message, get_position)


def get_position(message):
    staff_data[message.chat.id]['position'] = message.text
    bot.send_message(message.chat.id,
                     'Введите дату трудоустройства в формате "ДД.ММ.ГГГГ":')
    bot.register_next_step_handler(message, get_date_of_employment)


def convert_date_format(date_str):
    # Преобразуем строку в объект datetime
    date_obj = datetime.strptime(date_str, '%d.%m.%Y')
    # Форматируем объект datetime обратно в строку в нужном формате
    return date_obj.strftime('%Y-%m-%d')


def get_date_of_employment(message):
    # Пример простой проверки формата даты
    try:
        date_of_employment = convert_date_format(message.text)
        staff_data[message.chat.id]['date_of_employment'] = date_of_employment
        bot.send_message(message.chat.id,
                         'Введите день рождения в формате "ДД.ММ.ГГГГ":')
        bot.register_next_step_handler(message, get_day_of_birth)
    except ValueError:
        bot.send_message(message.chat.id,
                         "Пожалуйста, введите корректную дату (ДД.ММ.ГГГГ):")
        bot.register_next_step_handler(message, get_date_of_employment)


def get_day_of_birth(message):
    # Пример простой проверки формата даты
    try:
        day_of_birth = convert_date_format(message.text)
        staff_data[message.chat.id]['day_of_birth'] = day_of_birth
        bot.send_message(message.chat.id,
                         'Введите номер телефона (только цифры начиная с 8..:')
        bot.register_next_step_handler(message, get_phone_number)
    except ValueError:
        bot.send_message(message.chat.id,
                         "Пожалуйста, введите корректную дату (ДД.ММ.ГГГГ):")
        bot.register_next_step_handler(message, get_day_of_birth)


def get_phone_number(message):
    # Простой пример проверки формата номера телефона
    if not message.text.isdigit() or len(message.text) < 10:
        bot.send_message(message.chat.id,
                         "Пожалуйста, введите корректный номер телефона."
                         "Только цифры начиная с 8...:")
        bot.register_next_step_handler(message, get_phone_number)
        return
    staff_data[message.chat.id]['phone_number'] = message.text
    save_staff(message.chat.id)  # Сохраняем данные в базе данных


def save_staff(chat_id):
    data = staff_data[chat_id]
    db_data = [(None, data['name'], data['tabel_num'], data['position'],
                data['date_of_employment'], data['day_of_birth'],
                data['phone_number'])]
    # staff = [i for i in data.items()]
    try:
        db_record('''
                    INSERT INTO staff VALUES (?,?,?,?,?,?,?);
                ''', db_data)
        bot.send_message(chat_id, f'Сотрудник {data["name"]} добавлен успешно')
        bot.send_message(ADMIN_CHAT, f'Добавлен сотрудник - {data["name"]}')
    except Exception as e:
        bot.send_message(chat_id,
                         f'Ошибка при добавлении сотрудника: {e}')
    finally:
        staff_data.clear()


def del_staff(message):
    try:
        staff_name = message.text
        rows = db_read('''
            SELECT id FROM staff WHERE name = ?;
        ''', (staff_name,))

        if not rows:
            bot.send_message(message.chat.id, "Сотрудник не найден.")
            return
        staff_id = rows[0][0]
        db_record('''DELETE FROM staff WHERE id = ?;''',
                  (staff_id,), many=False)
        bot.send_message(message.chat.id, f"Сотрудник {staff_name} удален!")
        bot.send_message(ADMIN_CHAT, f'Сотрудник {staff_name} удален!')
    except Exception as e:
        bot.send_message(message.chat.id,
                         f'Ошибка при удалении сотрудника: {e}')


def check_birthdays():
    pass
    # """Проверяем дни рождения на следующие 3 дня"""
    # today = datetime.now()
    # for days_ahead in range(1, 23):  # 1, 2 и 3 дня вперед - (1, 4)
    #     date_to_check = today + timedelta(days=days_ahead)
    #     day_to_filter = date_to_check.strftime("%d")
    #     month_to_filter = date_to_check.strftime("%m")
    #     rows = db_read('''
    #         SELECT name, phone_number, date_of_birth
    #         FROM staff
    #         WHERE strftime('%d', date_of_birth) = ?
    #         AND strftime('%m', date_of_birth) = ?;
    #     ''', (day_to_filter, month_to_filter))
    #     if rows:  # Если есть строки
    #         for row in rows:
    #             birth = (
    #                 f'{day_to_filter}.{month_to_filter} день рождения '
    #                 f'сотрудника - {row[0]}!',
    #                 f'Ему исполнится {datetime.now().year - int(row[2][:4])}!')
    #             stacked.append(' '.join(birth))  # Объединяем строки в одну


def send_message(bot, message):
    # Получаем всех пользователей для отправки сообщений
    user_ids = db_read('SELECT chat_id FROM users')
    if current_time.weekday() == 2:    # if current_time.hour == 20:
        bot.send_message(ADMIN_CHAT, f'Кол-во зарегистрированных пользователей'
                                     f' - {len(user_ids)}')
    if stacked:  # Если есть сообщения для отправки
        for chat_id in user_ids:
            chat_id = chat_id[0]  # Извлекаем chat_id из кортежа
            for message in stacked:
                try:
                    bot.send_message(chat_id=chat_id, text=message)
                    time.sleep(1)  # Задержка между отправкой сообщений
                except Exception as e:
                    bot.send_message(
                        ADMIN_CHAT,
                        f"Произошла ошибка: {e} "
                        f"при отправке сообщения в чат {chat_id}")


def main():
    # Запускаем бота в отдельном потоке
    threading.Thread(target=bot.polling).start()
    while True:
        try:
            check_birthdays()
            if 9 <= current_time.hour <= 22 \
                    and current_time.weekday() not in (0, 2):
                send_message(bot, stacked)  # Отправляем сообщения
                stacked.clear()  # Очищаем стек сообщений
                time.sleep(86000)  # Ждем +-24 часа перед следующей проверкой
        except Exception as e:
            bot.send_message(ADMIN_CHAT, f"Произошла ошибка: {e}")
            time.sleep(60)  # Ждем 1 минуту перед повторной попыткой


if __name__ == "__main__":
    main()
