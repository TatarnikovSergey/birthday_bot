# from time import time
# import sys
from datetime import datetime, date, timedelta, time
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler

BIRTHDAY_DAD = datetime(1984, 5, 29)
BIRTHDAY_MOM = datetime(1986, 1, 13)
BIRTHDAY_LIZA = datetime(2015, 12, 21)
BIRTHDAY_VARYA = datetime(2012, 4, 11)

# current_day = date.today()
current_day = datetime.now()
# dad = datetime.combine(BIRTHDAY_DAD, time())
# print(datetime.time(datetime.now()))
# print(datetime.now())

last_digit_days = ('2', '3', '4')
last_digit_day = '1'
declination = {1: 'день', 234: 'дня', 567890: 'дней'}



def get_declination(count_days):
    if '10' < str(count_days)[-2:] <= '20' and len(str(count_days)) > 1:
        return declination[567890]
    elif str(count_days)[-1] in last_digit_days:
        return declination[234]
    elif str(count_days)[-1] == last_digit_day:
        return declination[1]
    else:
        return declination[567890]


def calculate_days(birthday):
    if current_day.strftime("%m-%d") < birthday.strftime("%m-%d"):
        result = birthday.day-current_day.day
        return f'День рождения через {result} {get_declination(result)}!' \
               f' Исполнится {(current_day.year-birthday.year)} лет'
    elif current_day.strftime("%m-%d") > birthday.strftime("%m-%d"):
        # next_year = birthday.replace(int(date.today().year + 1))  # прибавляем год
        next_year = datetime.replace(birthday, year=int(current_day.year + 1))
        result = (next_year - current_day).days
        # if result <= 3:

        return f'День рождения через {result} {get_declination(result)}!' \
               f' Исполнится {(next_year.year-birthday.year)} лет'#{a if str((next_year - current_day).days)[-1] in tr else c if str((next_year - current_day).days)[-1] == tr1 else b}'
    else:
        return 'Сегодня день рождения!'


print(calculate_days(BIRTHDAY_LIZA))
print(calculate_days(BIRTHDAY_DAD))
print(calculate_days(BIRTHDAY_MOM))
print(calculate_days(BIRTHDAY_VARYA))
# print(calculate_days(date(2020, 11, 10)))




if __name__ == '__main__':
    print('Программа расчета количества дней до дня рождения!')

    birthday = input('Введите дату рождения в формате "день.месяц.год". '
                     'Пример 5.12.1995 \nДля выхода введите "Q"  \n')
    birthday = datetime.strptime(birthday, '%d.%m.%Y')
    print(calculate_days(birthday))

