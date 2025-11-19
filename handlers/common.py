from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import Command

from config import ADMIN_ID
from db import (
    get_girlfriend_chat_id,
    set_girlfriend_chat_id,
    is_waiting_wish,
    set_waiting_wish,
    add_wish,
)
from keyboards import get_admin_keyboard, get_girlfriend_keyboard, GIRL_BTN_WANT

# Роутер для общих команд
router = Router()


@router.message(Command("start"))
async def start_handler(message: Message):
    # """
    # /start:
    # - для админа: показывает сервисное сообщение и админскую клавиатуру.
    # - для девушки: сохраняет её chat_id (если ещё не сохранён) и показывает кнопку "Хочу".
    # """
    user_id = message.from_user.id if message.from_user else None

    if user_id == ADMIN_ID:
        await message.answer(
            "Привет, админ! 👨‍💻\n\n"
            "Я готов отправлять напоминания.\n"
            "Команды:\n"
            "/add — добавить напоминание\n"
            "/list — список напоминаний\n"
            "/delete ID — отключить напоминание\n"
            "/send_random — отправить случайное напоминание девушке\n"
            "/reset — снова активировать все напоминания\n"
            "/wishes — список хотелок",
            reply_markup=get_admin_keyboard()
        )
        return

    # не админ — потенциально твоя девушка
    girlfriend_chat_id = await get_girlfriend_chat_id()

    if girlfriend_chat_id is None:
        await set_girlfriend_chat_id(message.chat.id)
        await message.answer(
            "Привет! 🥰\n\n"
            "Я бот, которого Серёжа сделал специально для тебя.\n"
            "Теперь у меня есть новая функция: можно добавлять свои хотелки 💫\n\n"
            "Нажми кнопку «Хочу» внизу, напиши, что ты хочешь (можно прикрепить ссылку или скриншот),\n"
            "и когда-нибудь это обязательно сбудется 💖",
            reply_markup=get_girlfriend_keyboard()
        )
    else:
        await message.answer(
            "Рада тебя снова видеть! 💖\n\n"
            "Если у тебя появилась новая хотелка — жми кнопку «Хочу» внизу 👇",
            reply_markup=get_girlfriend_keyboard()
        )


@router.message(Command("whoami"))
async def whoami_handler(message: Message):
    # """Обрабатывает команду /whoami — показывает ID пользователя."""
    await message.answer(
        f"Твой Telegram ID: `{message.from_user.id}`",
        parse_mode="Markdown"
    )

@router.message(F.text == GIRL_BTN_WANT)
async def girl_want_button_handler(message: Message):
    # """
    # Обрабатывает нажатие кнопки 'Хочу' от девушки.
    # Переводит бота в режим ожидания хотелки.
    # """
    # Если вдруг это нажал админ — игнорируем
    if message.from_user and message.from_user.id == ADMIN_ID:
        return

    girlfriend_chat_id = await get_girlfriend_chat_id()
    if girlfriend_chat_id is None or message.chat.id != girlfriend_chat_id:
        # Неизвестный пользователь — пока ничего не делаем
        return

    await set_waiting_wish(True)

    await message.answer(
        "Напиши, пожалуйста, что ты хочешь 💫\n\n"
        "Это может быть текст, ссылка, фотография или скриншот.\n"
        "Я всё сохраню и передам Серёже 💌"
    )

@router.message(F.from_user.id != ADMIN_ID)  # общий обработчик для сообщений девушки
async def girl_wish_message_handler(message: Message, bot: Bot):
    # """
    # Ловит сообщение от девушки, если бот сейчас ждёт от неё хотелку.
    # Сохраняет её в БД и шлёт уведомление админу.
    # """
    # Игнорируем админа
    if message.from_user and message.from_user.id == ADMIN_ID:
        return

    girlfriend_chat_id = await get_girlfriend_chat_id()
    if girlfriend_chat_id is None or message.chat.id != girlfriend_chat_id:
        # Не та пользовательница
        return

    # Проверяем, ждём ли сейчас хотелку
    waiting = await is_waiting_wish()
    if not waiting:
        # Обычное сообщение, не в режиме "Хочу" — не трогаем
        return

    # Сбрасываем флаг "ждём"
    await set_waiting_wish(False)

    # Собираем данные хотелки
    text = message.text or message.caption or None

    photo_file_id = None
    if message.photo:
        largest_photo = message.photo[-1]
        photo_file_id = largest_photo.file_id

    # Сохраняем в БД
    wish_id = await add_wish(
        user_id=message.from_user.id,
        text=text,
        photo_file_id=photo_file_id
    )

    # Подтверждение девушке
    await message.answer(
        "Я сохранила твою хотелку ✨\n"
        "Серёжа обязательно про неё узнает 💖"
    )

    # Уведомление админу
    from config import ADMIN_ID as ADMIN

    header = f"✨ Новая хотелка #{wish_id}\n\n"
    if text:
        header += f"Текст:\n{text}\n"

    if photo_file_id:
        # если есть фото — шлём фото с подписью
        await bot.send_photo(
            chat_id=ADMIN,
            photo=photo_file_id,
            caption=header
        )
    else:
        await bot.send_message(
            chat_id=ADMIN,
            text=header
        )
