# from birthday import get_staff, cancel_staff
# def cancel_insert(message, reset_timers, chat_id):
#     """Обработка отмены операции ввода данных."""
#     chat_id = message.chat.id
#     if message.text.strip() == '/cancel':# or chat_id not in reset_timers:
#         return cancel_staff(message)  # Обработка отмены
#     elif chat_id not in reset_timers:  # Если время на ввод истекло
#         return get_staff(message)
#     else:
#         reset_timers[chat_id].cancel()  # Иначе останавливаем таймер
#
# return cancel_staff(message) if message.text.strip() == '/cancel' elif