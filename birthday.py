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
# current_time = datetime.now()  # .time()

stacked = []
waiting_users = []
staff_data = {}
# staff_edit_id = []
staff_edit_data = {}

# создаем клавиатуры
keyboard_start = types.InlineKeyboardMarkup()
keyboard_crud = types.InlineKeyboardMarkup()
keyboard_staff = types.InlineKeyboardMarkup()
# создаем кнопки
button1 = types.InlineKeyboardButton('Зарегистрировать', callback_data='yes')
button2 = types.InlineKeyboardButton('Отказать', callback_data='no')
button3 = types.InlineKeyboardButton('Добавить', callback_data='add')
button4 = types.InlineKeyboardButton('Изменить', callback_data='edit')
button5 = types.InlineKeyboardButton('Удалить', callback_data='delete')
button6 = types.InlineKeyboardButton('Список сотрудников',
                                     callback_data='list_staff')
button7 = types.InlineKeyboardButton('ФИО', callback_data='fio')
button8 = types.InlineKeyboardButton('Должность', callback_data='position')
button9 = types.InlineKeyboardButton('Номер телефона', callback_data='phone')
# добавляем кнопки в клавиатуру
keyboard_start.add(button1, button2)
keyboard_crud.add(button3, button4, button5, button6)
keyboard_staff.add(button7, button8, button9)


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
    ''', (chat_id, full_name), many=False)
    except Exception as e:
        bot.send_message(ADMIN_CHAT, f'Ошибка добавления пользователя: {e}')


@bot.message_handler(commands=['start'])
def say_hi(message):
    """Получаем данные нового пользователя."""
    try:
        chat_id = message.chat.id
        full_name = message.from_user.full_name
        bot.send_message(chat_id=chat_id,
                         text=f'Приветствую Вас {full_name}. Это закрытый  Бот'
                              ' только для сотрудников ОКЭ. Если Вы не '
                              'сотрудник - Вам будет отказано в регистрации!')
        bot.send_message(ADMIN_CHAT,
                         f'Зарегистрировать пользователя {full_name}?',
                         reply_markup=keyboard_start)
        waiting_users.append((chat_id, full_name))
    except Exception as e:
        bot.send_message(ADMIN_CHAT,
                         f'Ошибка при получении данных о пользователе: {e}')


@bot.message_handler(commands=['crud'])
def crud_staff(message):
    """Отправляем кнопки CRUD."""
    if int(message.chat.id) == int(ADMIN_CHAT):
        bot.send_message(message.chat.id, "CRUD-операции с сотрудниками:",
                         reply_markup=keyboard_crud)
    else:
        bot.send_message(message.chat.id,
                         "Вы не являетесь администратором!")


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    """Обработка нажатий кнопок."""
    try:
        if call.data == 'yes':  # Если кнопка "Зарегистрировать" была нажата
            chat_id, full_name = waiting_users.pop(0)
            save_user(chat_id, full_name)
            bot.send_message(chat_id,
                             f'Вы зарегистрированы как {full_name}. '
                             f'Бот напомнит Вам о дне рождения '
                             f'сотрудника за 3 дня!')
            bot.send_message(ADMIN_CHAT,
                             f'Пользователь {full_name} зарегистрирован!')
        elif call.data == 'no':  # Если кнопка "Отказать" была нажата
            chat_id, full_name = waiting_users.pop(0)  # Достаем пользователя
            bot.send_message(chat_id,
                             f'Вам отказано в регистрации как {full_name}, '
                             f'поскольку Вы не являетесь сотрудником.')
        elif call.data == 'add':
            bot.send_message(call.message.chat.id,
                             "Добавление нового сотрудника:")
            bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                          message_id=call.message.message_id,
                                          reply_markup=None)
            staff_data[call.message.chat.id] = {}  # Инициируем словарь данных
            bot.send_message(call.message.chat.id, "Введите ФИО сотрудника:")
            bot.register_next_step_handler(call.message, get_name)
        elif call.data == 'delete':
            bot.send_message(call.message.chat.id,
                             "Введите имя сотрудника для удаления:")
            bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                          message_id=call.message.message_id,
                                          reply_markup=None)
            bot.register_next_step_handler(call.message, del_staff)
        elif call.data == 'list_staff':
            get_list_staff(call)
            bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                          message_id=call.message.message_id,
                                          reply_markup=None)
        elif call.data == 'edit':
            bot.send_message(call.message.chat.id,
                             "Введите ФИО сотрудника для редактирования:")
            bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                          message_id=call.message.message_id,
                                          reply_markup=None)
            staff_data[call.message.chat.id] = {}
            bot.register_next_step_handler(call.message, edit_staff)
        elif call.data == 'fio':
            bot.send_message(call.message.chat.id,
                             "Введите новое значение для ФИО:")
            bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                          message_id=call.message.message_id,
                                          reply_markup=None)
            bot.register_next_step_handler(call.message, get_name, 'name')
        elif call.data == 'position':
            bot.send_message(call.message.chat.id,
                             "Введите новое значение для Должности:")
            bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                          message_id=call.message.message_id,
                                          reply_markup=None)
            bot.register_next_step_handler(call.message,
                                           update_field, 'position')
        elif call.data == 'phone':
            bot.send_message(call.message.chat.id,
                             "Введите новое значение для Номера телефона:")
            bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                          message_id=call.message.message_id,
                                          reply_markup=None)
            bot.register_next_step_handler(call.message,
                                           get_phone_number, 'phone_number')
        # Удаляем callback_query, чтобы не повторялась

        bot.answer_callback_query(callback_query_id=call.id)
    except Exception as e:
        bot.send_message(ADMIN_CHAT, f'Ошибка обработки кнопок: {e}')


@bot.message_handler(func=lambda msg: msg.text)
def get_staff(message):
    """Инфо о сотруднике."""
    find = message.text.strip()
    # rows = db_read('''
    #     SELECT * FROM staff WHERE name = ?;
    # ''', (find,))
    rows= db_read('''
            SELECT * FROM staff WHERE name LIKE ?;
        ''', (f'{find}%',))
    if not rows:
        bot.send_message(message.chat.id, 'Сотрудник не найден.')
        return
    staff_info_list = []
    for row in rows:
        staff_data = {
            'ФИО': row[1],
            'Должность': row[3],
            'Табельный номер': row[2],
            'Дата устройства': row[4],
            'День рождения': row[5],
            'Номер телефона': convert_phone_number(row[6])
        }
        staff_info = '\n'.join([f'{key}: {value}' for key, value in staff_data.items()])
        staff_info_list.append(staff_info)
    # Объединяем информацию о всех сотрудниках в одно сообщение
    all_staff_info = '\n\n'.join(staff_info_list)
    bot.send_message(message.chat.id,
                     f'Информация о сотруднике:\n{all_staff_info}')


def edit_staff(message):
    """Обновление сотрудника."""
    try:
        staff_name = message.text.strip()
        rows = db_read('''
            SELECT * FROM staff WHERE name LIKE ?;
        ''', (f'{staff_name}%',))
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
                         "Выберите поле для редактирования:\n",
                         reply_markup=keyboard_staff)
    except Exception as e:
        bot.send_message(message.chat.id,
                         f"Произошла ошибка при обновлении: {e}")


def update_field(message, field_db_name):
    """Обновление поля сотрудника."""
    try:
        new_value = message.text.strip()
        staff_edit_id = staff_edit_data[message.chat.id]['edit_id']
        query = f'''
            UPDATE staff SET {field_db_name} = ? WHERE id = ?;
        '''
        params = (new_value, staff_edit_id)
        db_record(query, params, many=False)
        bot.send_message(message.chat.id, "Данные успешно обновлены.")
        staff_edit_data.clear()
        staff_edit_id = None
    except Exception as e:
        bot.send_message(message.chat.id,
                         f"Произошла ошибка при обновлении: {e}")


def get_list_staff(call):
    """Получение списка сотрудников."""
    try:
        staff_list = db_read('''
                SELECT name, position, phone_number
                FROM staff
                ORDER BY name ASC;
                ''')
         # Форматируем список сотрудников в строку по формату: Фамилия И.О.
        if staff_list:
            staff_message = 'Список сотрудников:\n'
            for staff in staff_list:
                fio = staff[0].split()
                short_fio = f'{fio[0]} {fio[1][0]}.' \
                            f'{fio[2][0] if len(fio) >= 3 else None}.'
                staff_message += f'{short_fio}\n ' \
                                 f'{convert_phone_number(staff[2])}\n \n'
        else:
            staff_message = 'Список сотрудников пуст.'
            # Разбиваем сообщение на части, если оно слишком длинное
        max_length = 4096
        if len(staff_message) > max_length:
            for i in range(0, len(staff_message), max_length):
                bot.send_message(call.message.chat.id,
                                 staff_message[i:i + max_length])
        else:
            # Отправляем сообщение с полным списком сотрудников
            bot.send_message(call.message.chat.id, staff_message)
    except Exception as e:
        bot.send_message(ADMIN_CHAT,
                         f'Ошибка получения списка сотрудников: {e}')


def get_name(message, upd=None):
    """Добавление/изменение ФИО."""
    name = message.text.strip()
    if len(name.split()) <= 1 or any(i.isdigit() for i in name):
        bot.send_message(message.chat.id, "Введите корректное ФИО:")
        bot.register_next_step_handler(message, get_name,
                                       'name' if upd else None)
        return
    if upd:
        return update_field(message, 'name')
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


def get_phone_number(message, upd=None):
    # Простой пример проверки формата номера телефона
    if not message.text.isdigit() or len(message.text) < 10:
        bot.send_message(message.chat.id,
                         "Пожалуйста, введите корректный номер телефона."
                         "Только цифры начиная с 8...:")
        bot.register_next_step_handler(message, get_phone_number,
                                       'phone_number' if upd else None)
        return
    if upd:
        return update_field(message, 'phone_number')
    staff_data[message.chat.id]['phone_number'] = message.text
    save_staff(message.chat.id)  # Сохраняем данные в базе данных


def save_staff(chat_id):
    data = staff_data[chat_id]
    db_data = [(None, data['name'], data['tabel_num'], data['position'],
                data['date_of_employment'], data['day_of_birth'],
                data['phone_number'])]
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


def convert_phone_number(phone_number):
    if phone_number.startswith('8'):
        return '+7' + phone_number[1:]  # Заменяем 8 на +7
    return phone_number  # Если номер уже в правильном формате


def check_birthdays():
    """Проверяем дни рождения на следующие 3 дня"""
    today = datetime.now()
    for days_ahead in range(2, 7):  # 1, 2 и 3 дня вперед - (1, 4)
        date_to_check = today + timedelta(days=days_ahead)
        day_to_filter = date_to_check.strftime("%d")
        month_to_filter = date_to_check.strftime("%m")
        rows = db_read('''
            SELECT name, phone_number, date_of_birth
            FROM staff
            WHERE strftime('%d', date_of_birth) = ?
            AND strftime('%m', date_of_birth) = ?;
        ''', (day_to_filter, month_to_filter))
        if rows:  # Если есть строки
            for row in rows:
                age = datetime.now().year - int(row[2][:4])
                phone_number = convert_phone_number(row[1])
                birth = (
                    f'{day_to_filter}.{month_to_filter} день рождения '
                    f'сотрудника - <b>{row[0]}</b>!',
                    f'Ему исполнится {age}!'
                    # f' Поздравить - {phone_number}'
                )
                stacked.append(' '.join(birth))# Объединяем строки в одну


def today_birthday():
    """Проверяем дни рождения на сегодня."""
    today = datetime.now()
    day_to_filter = today.strftime("%d")
    month_to_filter = today.strftime("%m")
    rows = db_read('''
            SELECT name, phone_number, date_of_birth
            FROM staff
            WHERE strftime('%d', date_of_birth) = ?
            AND strftime('%m', date_of_birth) = ?;
        ''', (day_to_filter, month_to_filter))
    if rows:  # Если есть строки
        for row in rows:
            age = datetime.now().year - int(row[2][:4])
            phone_number = convert_phone_number(row[1])
            birth = (
                f'Сегодня день рождения '
                f'сотрудника - <b>{row[0]}</b>!',
                f'Ему исполняется {age}!'
                f' Поздравить: <b>{phone_number}</b>'
            )
            stacked.append(' '.join(birth))# Объединяем строки в одну


def send_message(bot, message):
    # Получаем всех пользователей для отправки сообщений
    user_ids = db_read('SELECT chat_id FROM users')
    if datetime.now().weekday() == 0:    # if current_time.hour == 20:
        bot.send_message(ADMIN_CHAT, f'Кол-во зарегистрированных пользователей'
                                     f' - {len(user_ids)}')
    if stacked:  # Если есть сообщения для отправки
        for chat_id in user_ids:
            chat_id = chat_id[0]  # Извлекаем chat_id из кортежа
            for message in stacked:
                try:
                    bot.send_message(chat_id=chat_id, text=message,
                                     parse_mode='HTML')
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
            current_time = datetime.now()
            if current_time.hour == 9 and 57 < current_time.minute <= 59:
                today_birthday()
                check_birthdays()
                send_message(bot, stacked)  # Отправляем сообщения
                stacked.clear()  # Очищаем стек сообщений
                time.sleep(86400)  # Ждем +-24 часа перед следующей проверкой
        except Exception as e:
            bot.send_message(ADMIN_CHAT, f"Произошла ошибка: {e}")
            time.sleep(60)  # Ждем 1 минуту перед повторной попыткой


if __name__ == "__main__":
    main()
