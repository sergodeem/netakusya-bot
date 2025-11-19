from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Тексты кнопок для админа
ADMIN_BTN_SEND = "❤️ Отправить напоминание"
ADMIN_BTN_LIST = "📋 Список напоминаний"
ADMIN_BTN_RESET = "🔁 Активировать все"


def get_admin_keyboard() -> ReplyKeyboardMarkup:
    # """
    # Возвращает клавиатуру для админа с основными командами.
    # """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ADMIN_BTN_SEND)],
            [
                KeyboardButton(text=ADMIN_BTN_LIST),
                KeyboardButton(text=ADMIN_BTN_RESET),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
    return keyboard
