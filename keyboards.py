from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# --- КНОПКИ ДЛЯ АДМИНА ---

ADMIN_BTN_SEND = "❤️ Отправить напоминание"
ADMIN_BTN_LIST = "📋 Список напоминаний"
ADMIN_BTN_RESET = "🔁 Активировать все"
ADMIN_BTN_WISHES = "💭 Хотелки"


def get_admin_keyboard() -> ReplyKeyboardMarkup:
    # """
    # Клавиатура для админа с основными командами.
    # """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ADMIN_BTN_SEND)],
            [
                KeyboardButton(text=ADMIN_BTN_LIST),
                KeyboardButton(text=ADMIN_BTN_RESET),
            ],
            [KeyboardButton(text=ADMIN_BTN_WISHES)],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
    return keyboard


# --- КНОПКА ДЛЯ ДЕВУШКИ ---

GIRL_BTN_WANT = "✨ Хочу"


def get_girlfriend_keyboard() -> ReplyKeyboardMarkup:
    # """
    # Клавиатура для девушки с кнопкой 'Хочу'.
    # """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=GIRL_BTN_WANT)],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
    return keyboard

