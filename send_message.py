import os
import time

import telebot
from dotenv import load_dotenv

load_dotenv()

ADMIN_CHAT = os.getenv('ADMIN_CHAT_ID')
API_TOKEN = os.getenv('T_TOKEN')
bot = telebot.TeleBot(API_TOKEN)


def send_message(chat_id, message):
    try:
        bot.send_message(chat_id=chat_id, text=message,
                         parse_mode='HTML')
        time.sleep(1)  # Задержка между отправкой сообщений
    except Exception as e:
        bot.send_message(
            ADMIN_CHAT,
            f"Произошла ошибка: {e} "
            f"при отправке сообщения в чат {chat_id}")
