import logging
import os
import sys
import threading
import time
from datetime import datetime, timedelta

import telebot
from telebot import apihelper
from dotenv import load_dotenv

from keyboarbs import keyboard_start, keyboard_crud, keyboard_staff
from parameters import TIME_ADD_STAFF, TIME_DEL_STAFF, TIME_EDIT_STAFF, \
    max_length_message, DAYS_CHECK, MES_HOUR, MES_MINUTE, \
    DAY_TO_INFO_COUN_USERS
from working_db import db_read, db_write, save_user

load_dotenv()

ADMIN_CHAT = os.getenv('ADMIN_CHAT_ID')
API_TOKEN = os.getenv('T_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

logging.basicConfig(
    level=logging.WARNING,
    filename='birthday.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(funcName)s'
)
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)

stacked = []
waiting_users = []
staff_data = {}
staff_edit_data = {}
reset_timers = {}


def send_message(chat_id, message, reply_markup=None):
    """Отправка сообщений в чат."""
    try:
        bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML',
                         reply_markup=reply_markup)
        time.sleep(1)  # Задержка между отправкой сообщений
    except apihelper.ApiException as e:
        bot.send_message(ADMIN_CHAT, f"Произошла ошибка: {e} "
                                     f"при отправке сообщения в чат {chat_id}")
        logger.error(f'Ошибка {e} отправки сообщения {message} '
                     f'{reply_markup if reply_markup else None}')


@bot.message_handler(commands=['start'])
def say_hi(message):
    """Получаем данные нового пользователя."""
    try:
        chat_id = message.chat.id
        full_name = message.from_user.full_name
        send_message(chat_id, f'Приветствую Вас {full_name}. Это закрытый  Бот'
                              ' только для сотрудников ОКЭ. Если Вы не '
                              'сотрудник - Вам будет отказано в регистрации!')
        send_message(ADMIN_CHAT, f'Зарегистрировать пользователя {full_name}?',
                     reply_markup=keyboard_start)
        waiting_users.append((chat_id, full_name))
    except Exception as e:
        send_message(ADMIN_CHAT,
                     f'Ошибка при получении данных о пользователе: {e}')
        logger.error(f'Ошибка {e} при получении данных о пользователе'
                     f'в процессе  обработке сообщения {message}')


@bot.message_handler(commands=['crud'])
def crud_staff(message):
    """Отправляем кнопки CRUD."""
    if int(message.chat.id) == int(ADMIN_CHAT):
        send_message(message.chat.id, "CRUD-операции с сотрудниками:",
                     reply_markup=keyboard_crud)
    else:
        send_message(message.chat.id, "Вы не являетесь администратором!")


@bot.message_handler(commands=['cancel'])
def cancel_staff(message):
    """Отмена ввода данных."""
    if not isinstance(message, int):
        chat_id = message.chat.id
    else:
        chat_id = message
    if chat_id in staff_data:
        del staff_data[chat_id]  # Удаляем данные о сотруднике
        if chat_id in reset_timers:
            reset_timers[chat_id].cancel()
            del reset_timers[chat_id]  # Удаляем таймер
        send_message(chat_id, "Ввод отменен. Вы можете ввести любую команду.")
    else:
        send_message(chat_id, "Нет активного ввода для отмены.")


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    """Обработка нажатий кнопок."""
    try:
        chat_id = call.message.chat.id
        if call.data == 'yes':  # Если кнопка "Зарегистрировать" была нажата
            chat_id_user, full_name = waiting_users.pop(0)
            save_user(chat_id_user, full_name)
            send_message(chat_id_user, f'Вы зарегистрированы как {full_name}. '
                                       f'Бот напомнит Вам о дне рождения '
                                       f'сотрудника за 3 дня!')
            send_message(ADMIN_CHAT,
                         f'Пользователь {full_name} зарегистрирован!')
        elif call.data == 'no':  # Если кнопка "Отказать" была нажата
            chat_id_user, full_name = waiting_users.pop(
                0)  # Достаем пользователя
            send_message(chat_id_user,
                         f'Вам отказано в регистрации как {full_name}, '
                         f'поскольку Вы не являетесь сотрудником.')
        elif call.data == 'add':
            send_message(chat_id, "Добавление нового сотрудника:")
            staff_data[chat_id] = {}  # Инициируем словарь данных
            send_message(chat_id, "Введите ФИО сотрудника:")

            reset_timers[chat_id] = threading.Timer(TIME_ADD_STAFF, cancel_staff, [
                chat_id])  # Устанавливаем таймер
            reset_timers[chat_id].start()
            bot.register_next_step_handler(call.message, get_name)
            # Запускаем таймер
        elif call.data == 'delete':
            send_message(chat_id, "Введите имя сотрудника для удаления:")
            reset_timers[chat_id] = threading.Timer(TIME_DEL_STAFF, cancel_staff, [
                chat_id])  # Устанавливаем таймер
            reset_timers[chat_id].start()
            bot.register_next_step_handler(call.message, del_staff)
        elif call.data == 'list_staff':
            get_list_staff(call)
        elif call.data == 'edit':
            send_message(chat_id, "Введите ФИО сотрудника для редактирования:")
            staff_data[call.message.chat.id] = {}
            reset_timers[chat_id] = threading.Timer(
                TIME_EDIT_STAFF, cancel_staff, [chat_id])  # Устанавливаем таймер
            reset_timers[chat_id].start()
            bot.register_next_step_handler(call.message, edit_staff)
        elif call.data == 'fio':
            send_message(chat_id, "Введите новое значение для ФИО:")
            bot.register_next_step_handler(call.message, get_name, 'name')
        elif call.data == 'position':
            send_message(chat_id, "Введите новое значение для Должности:")
            bot.register_next_step_handler(call.message,
                                           update_field, 'position')
        elif call.data == 'phone':
            send_message(chat_id, "Введите новый номер телефона:")
            bot.register_next_step_handler(call.message,
                                           get_phone_number, 'phone_number')
        bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                      message_id=call.message.message_id,
                                      reply_markup=None)
        # Удаляем callback_query, чтобы не повторялась
        bot.answer_callback_query(callback_query_id=call.id)
    except apihelper.ApiException as e:
        send_message(ADMIN_CHAT, f'Ошибка обработки кнопок: {e}')
        logger.error(f'Ошибка {e} обработки кнопок при вызове {call}')


@bot.message_handler(func=lambda msg: msg.text)
def get_staff(message):
    """Инфо о сотруднике."""
    try:
        find = message.text.strip()
        rows = db_read('''
                SELECT * FROM staff WHERE name LIKE ?;
            ''', (f'{find}%',))
        if not rows:
            send_message(message.chat.id, 'Сотрудник не найден.')
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
            staff_info = '\n'.join(
                [f'{key}: {value}' for key, value in staff_data.items()])
            staff_info_list.append(staff_info)
        # Объединяем информацию о всех сотрудниках в одно сообщение
        all_staff_info = '\n\n'.join(staff_info_list)
        send_message(message.chat.id,
                     f'Информация о сотруднике:\n{all_staff_info}')
    except Exception as e:
        send_message(ADMIN_CHAT,
                     f'Ошибка получения информации о сотрудниках: {e}')


def edit_staff(message):
    """Обновление сотрудника."""
    if cancel_insert(message, reset_timers) is not None:
        return  # Если была отмена ввода - выходим
    try:
        staff_name = message.text.strip()
        rows = db_read('''
            SELECT * FROM staff WHERE name LIKE ?;
        ''', (f'{staff_name}%',))
        if not rows:
            send_message(message.chat.id, "Сотрудник не найден.")
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
        send_message(message.chat.id,
                     f"Что вы хотите изменить?:\n{staff_data}\n"
                     "Выберите поле для редактирования:\n",
                     reply_markup=keyboard_staff)
    except Exception as e:
        send_message(message.chat.id,
                     f"Произошла ошибка при обновлении: {e}")
        logger.error(f'Ошибка {e} при изменении данных о сотруднике'
                     f'в процессе  обработке сообщения {message}')
    reset_timers[message.chat.id].cancel()  # Останавливаем таймер


def update_field(message, field_db_name):
    """Обновление поля сотрудника."""
    if cancel_insert(message, reset_timers) is not None:
        return  # Если была отмена ввода - выходим
    try:
        new_value = message.text.strip()
        staff_edit_id = staff_edit_data[message.chat.id]['edit_id']
        query = f'''
            UPDATE staff SET {field_db_name} = ? WHERE id = ?;
        '''
        params = (new_value, staff_edit_id)
        db_write(query, params, many=False)
        send_message(message.chat.id, "Данные успешно обновлены.")
        staff_edit_data.clear()
        staff_edit_id = None
    except Exception as e:
        send_message(message.chat.id, f"Произошла ошибка при обновлении: {e}")
        logger.error(f'Ошибка {e} при изменении данных сотрудника'
                     f'в процессе  обработке сообщения {message}')


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
                staff_message += f'{short_fio} - ' \
                                 f'{convert_phone_number(staff[2])}\n'
            staff_message += f'<b>Всего сотрудников - {len(staff_list)}</b>'
        else:
            staff_message = 'Список сотрудников пуст.'
            # Разбиваем сообщение на части, если оно слишком длинное
        if len(staff_message) > max_length_message:
            for i in range(0, len(staff_message), max_length_message):
                send_message(call.message.chat.id,
                             staff_message[i:i + max_length_message])
        else:
            # Отправляем сообщение с полным списком сотрудников
            send_message(call.message.chat.id, staff_message)
    except Exception as e:
        send_message(ADMIN_CHAT, f'Ошибка получения списка сотрудников: {e}')


def cancel_insert(message, reset_timers):
    """Обработка отмены операции ввода данных или истечения времени."""
    chat_id = message.chat.id
    if message.text.strip() == '/cancel':  # Если нажали отмену:
        return cancel_staff(message), True  # обработка отмены
    elif chat_id not in reset_timers:  # Если время на ввод истекло:
        return get_staff(message) if message.text[0] != '/' \
            else crud_staff(message), True
    # else:
    #     reset_timers[chat_id].cancel()  # Иначе останавливаем таймер


def get_name(message, upd=None):
    """Добавление/изменение ФИО."""
    if cancel_insert(message, reset_timers) is not None:
        return  # Если была отмена ввода - выходим
    name = message.text.strip()
    if len(name.split()) <= 1 or any(i.isdigit() for i in name):
        send_message(message.chat.id, "Введите корректное ФИО:")
        bot.register_next_step_handler(message, get_name,
                                       'name' if upd else None)
        return
    if upd:
        return update_field(message, 'name')
    staff_data[message.chat.id]['name'] = name
    send_message(message.chat.id, "Введите табельный номер:")
    bot.register_next_step_handler(message, get_tabel_num)


def get_tabel_num(message):
    if cancel_insert(message, reset_timers) is not None:
        return  # Если была отмена ввода - выходим
    if not message.text.isdigit():
        send_message(message.chat.id,
                     "Введите корректный табельный номер (число):")
        bot.register_next_step_handler(message, get_tabel_num)
        return
    staff_data[message.chat.id]['tabel_num'] = message.text
    send_message(message.chat.id, "Введите должность:")
    bot.register_next_step_handler(message, get_position)


def get_position(message):
    if cancel_insert(message, reset_timers) is not None:
        return  # Если была отмена ввода - выходим
    staff_data[message.chat.id]['position'] = message.text
    send_message(message.chat.id,
                 'Введите дату трудоустройства в формате "ДД.ММ.ГГГГ":')
    bot.register_next_step_handler(message, get_date_of_employment)


def convert_date_format(date_str):
    # Преобразуем строку в объект datetime
    date_obj = datetime.strptime(date_str, '%d.%m.%Y')
    # Форматируем объект datetime обратно в строку в нужном формате
    return date_obj.strftime('%Y-%m-%d')


def get_date_of_employment(message):
    if cancel_insert(message, reset_timers) is not None:
        return  # Если была отмена ввода - выходим
    try:
        date_of_employment = convert_date_format(message.text)
        staff_data[message.chat.id]['date_of_employment'] = date_of_employment
        send_message(message.chat.id,
                     'Введите день рождения в формате "ДД.ММ.ГГГГ":')
        bot.register_next_step_handler(message, get_day_of_birth)
    except ValueError:
        send_message(message.chat.id,
                     'Пожалуйста, введите корректную дату (ДД.ММ.ГГГГ):')
        bot.register_next_step_handler(message, get_date_of_employment)


def get_day_of_birth(message):
    if cancel_insert(message, reset_timers) is not None:
        return  # Если была отмена ввода - выходим
    try:
        day_of_birth = convert_date_format(message.text)
        staff_data[message.chat.id]['day_of_birth'] = day_of_birth
        send_message(message.chat.id,
                     'Введите номер телефона (только цифры начиная с 8..:')
        bot.register_next_step_handler(message, get_phone_number)
    except ValueError:
        send_message(message.chat.id,
                     'Пожалуйста, введите корректную дату (ДД.ММ.ГГГГ):')
        bot.register_next_step_handler(message, get_day_of_birth)


def get_phone_number(message, upd=None):
    if cancel_insert(message, reset_timers) is not None:
        return  # Если была отмена ввода - выходим
    if not message.text.isdigit() or len(message.text) < 10 or \
            message.text[0] != '8':
        send_message(message.chat.id,
                     'Пожалуйста, введите корректный номер телефона.'
                     'Только цифры начиная с 8...:')
        bot.register_next_step_handler(message, get_phone_number,
                                       'phone_number' if upd else None)
        return
    if upd:
        return update_field(message, 'phone_number')
    staff_data[message.chat.id]['phone_number'] = message.text
    save_staff(message.chat.id)  # Сохраняем данные в базе данных
    reset_timers[message.chat.id].cancel()  # Останавливаем таймер


def save_staff(chat_id):
    data = staff_data[chat_id]
    db_data = [(None, data['name'], data['tabel_num'], data['position'],
                data['date_of_employment'], data['day_of_birth'],
                data['phone_number'])]
    try:
        db_write('''INSERT INTO staff VALUES (?,?,?,?,?,?,?); ''', db_data)
        send_message(chat_id, f'Сотрудник {data["name"]} добавлен успешно')
        send_message(ADMIN_CHAT, f'Добавлен сотрудник - {data["name"]}')
    except Exception as e:
        send_message(chat_id, f'Ошибка при добавлении сотрудника: {e}')
        logger.error(f'Ошибка {e} при сохранении сотрудника {data["name"]}')
    finally:
        staff_data.clear()


def del_staff(message):
    if cancel_insert(message, reset_timers) is not None:
        return  # Если была отмена ввода - выходим
    try:
        staff_name = message.text
        rows = db_read('''SELECT id FROM staff WHERE name = ?;''',
                       (staff_name,))
        if not rows:
            send_message(message.chat.id, "Сотрудник не найден.")
            return
        staff_id = rows[0][0]
        db_write('''DELETE FROM staff WHERE id = ?;''',
                 (staff_id,), many=False)
        send_message(message.chat.id, f"Сотрудник {staff_name} удален!")
        send_message(ADMIN_CHAT, f'Сотрудник {staff_name} удален!')
    except Exception as e:
        send_message(message.chat.id, f'Ошибка при удалении сотрудника: {e}')
    reset_timers[message.chat.id].cancel()  # Останавливаем таймер


def convert_phone_number(phone_number):
    if phone_number.startswith('8'):
        return '+7' + phone_number[1:]  # Заменяем 8 на +7
    return phone_number  # Если номер уже в правильном формате


def check_birthdays():
    """Проверяем дни рождения на несколько дней"""
    today_date = datetime.now()
    for days_ahead in range(0, DAYS_CHECK+1):  # 1, 2 и 3 дня вперед - (1, 4)
        date_to_check = today_date + timedelta(days=days_ahead)
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
                today = datetime.now().day == int(day_to_filter)
                date_message = 'Сегодня' if today else f'{day_to_filter}.' \
                                                       f'{month_to_filter}'
                birth = (
                    f'{date_message} день рождения ',
                    f'сотрудника - <b>{row[0]}</b>!',
                    f'Ему исполн%s {age}!' % ('яется' if today else 'ится'),
                    f' Поздравить: <b>{phone_number}</b>' if today else ''
                )
                stacked.append(' '.join(birth))  # Объединяем строки в одну


def birthday_messages(message):
    # Получаем всех пользователей для отправки сообщений
    user_ids = db_read('SELECT chat_id FROM users')
    if datetime.now().weekday() == DAY_TO_INFO_COUN_USERS:
        send_message(ADMIN_CHAT, f'Кол-во зарегистрированных пользователей'
                                 f' - {len(user_ids)}')
    if stacked:  # Если есть сообщения для отправки
        for chat_id in user_ids:
            chat_id = chat_id[0]  # Извлекаем chat_id из кортежа
            for message in stacked:
                send_message(chat_id, message)


def get_birthdays():
    last_run_time = datetime.now() - timedelta(days=1)
    while True:
        try:
            current_time = datetime.now()
            if current_time - last_run_time >= timedelta(days=1) and \
                current_time.hour == MES_HOUR and \
                    current_time.minute >= MES_MINUTE:
                last_run_time = current_time  # Обновляем время последнего запуска
                check_birthdays()
                birthday_messages(stacked)  # Отправляем сообщения
                stacked.clear()  # Очищаем стек сообщений
            time.sleep(60)  # Ждем +-24 часа перед следующей проверкой
        except Exception as e:
            send_message(ADMIN_CHAT, f"Произошла ошибка: {e}")
            logger.error(f'Ошибка {e} при получении дней рождения')
            time.sleep(60)  # Ждем 1 минуту перед повторной попыткой


def main():
    # Запускаем бота в отдельном потоке
    threading.Thread(target=get_birthdays).start()
    try:
        bot.infinity_polling()
    except Exception as e:
        bot.send_message(ADMIN_CHAT, f"Произошла ошибка: {e}")
        logger.error(f'Ошибка в работе программы{e}')


if __name__ == "__main__":
    main()
