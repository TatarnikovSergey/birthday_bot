from telebot import types


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
