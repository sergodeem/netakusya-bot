from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import Command

from config import ADMIN_ID
from db import (
    add_reminder,
    list_reminders,
    deactivate_reminder,
    get_girlfriend_chat_id,
    get_random_active_reminder,
    activate_all_reminders,
    list_wishes,
)
from keyboards import (
    ADMIN_BTN_SEND,
    ADMIN_BTN_LIST,
    ADMIN_BTN_RESET,
    ADMIN_BTN_WISHES,
)

router = Router()


def is_admin(message: Message) -> bool:
    # """Проверяет, является ли пользователь админом."""
    return message.from_user and message.from_user.id == ADMIN_ID


# --- /add ---


@router.message(Command("add"))
async def add_handler(message: Message):
    # """
    # /add — добавить напоминание (только админ).

    # Работает:
    # - как текст: /add я тебя люблю
    # - как фото с подписью: (фото) + подпись '/add ...'
    # """
    if not is_admin(message):
        return await message.answer("Эта команда только для админа 😇")

    raw = message.text or message.caption
    if not raw:
        return await message.answer(
            "Использование: `/add текст напоминания`\n"
            "Можно отправить просто текст или фото с подписью.",
            parse_mode="Markdown",
        )

    parts = raw.split(" ", 1)
    if len(parts) < 2 or not parts[1].strip():
        return await message.answer(
            "После команды нужно написать текст.\n\n"
            "Пример:\n`/add ты самая лучшая на свете 💖`",
            parse_mode="Markdown",
        )

    text = parts[1].strip()

    photo_file_id = None
    if message.photo:
        largest_photo = message.photo[-1]
        photo_file_id = largest_photo.file_id

    reminder_id = await add_reminder(text=text, photo_file_id=photo_file_id)

    desc = []
    if text:
        desc.append("📝 текст")
    if photo_file_id:
        desc.append("🖼 фото")
    desc_str = " + ".join(desc) if desc else "пустое напоминание"

    await message.answer(
        f"Напоминание сохранено ✅\n"
        f"ID: {reminder_id}\n"
        f"Состав: {desc_str}"
    )


# --- /list + кнопка 'Список напоминаний' ---


@router.message(Command("list"))
@router.message(F.text == ADMIN_BTN_LIST)
async def list_handler(message: Message):
    # """Показывает список напоминаний (только админ)."""
    if not is_admin(message):
        return await message.answer("Эта команда только для админа 😇")

    reminders = await list_reminders()
    if not reminders:
        return await message.answer("Пока нет ни одного напоминания.")

    lines = []
    for r_id, text, photo_file_id, is_active in reminders:
        status = "✅" if is_active else "🚫"
        if photo_file_id and text:
            kind = "🖼+📝"
        elif photo_file_id:
            kind = "🖼"
        else:
            kind = "📝"

        short_text = text if text else "(без текста)"
        if len(short_text) > 40:
            short_text = short_text[:37] + "..."

        lines.append(f"{r_id}. {status} {kind} {short_text}")

    await message.answer("Твои напоминания:\n\n" + "\n".join(lines))


# --- /delete ---


@router.message(Command("delete"))
async def delete_handler(message: Message):
    # """Отключает напоминание по ID (только админ)."""
    if not is_admin(message):
        return await message.answer("Эта команда только для админа 😇")

    raw = message.text or message.caption
    parts = raw.split(" ", 1) if raw else []
    if len(parts) < 2 or not parts[1].strip():
        return await message.answer(
            "Использование: `/delete ID`\nПример: `/delete 1`",
            parse_mode="Markdown",
        )

    try:
        reminder_id = int(parts[1].strip())
    except ValueError:
        return await message.answer("ID должен быть числом.")

    success = await deactivate_reminder(reminder_id)
    if success:
        await message.answer(f"Напоминание с ID {reminder_id} отключено 🚫")
    else:
        await message.answer(f"Не нашёл напоминание с ID {reminder_id}.")


# --- /send_random + кнопка 'Отправить напоминание' ---


@router.message(Command("send_random"))
@router.message(F.text == ADMIN_BTN_SEND)
async def send_random_handler(message: Message, bot: Bot):
    # """
    # Отправляет девушке случайное активное напоминание.
    # После отправки помечает его как неактивное.
    # """
    if not is_admin(message):
        return await message.answer("Эта команда только для админа 😇")

    girlfriend_chat_id = await get_girlfriend_chat_id()
    if girlfriend_chat_id is None:
        return await message.answer(
            "Я ещё не знаю chat_id девушки 🥺\n"
            "Пусть она напишет этому боту команду /start хотя бы один раз."
        )

    reminder = await get_random_active_reminder()
    if reminder is None:
        return await message.answer(
            "Нет активных напоминаний 😢\n"
            "Добавь хотя бы одно через `/add`.",
            parse_mode="Markdown",
        )

    r_id, text, photo_file_id = reminder

    if photo_file_id:
        await bot.send_photo(
            chat_id=girlfriend_chat_id,
            photo=photo_file_id,
            caption=text or None,
        )
    else:
        await bot.send_message(
            chat_id=girlfriend_chat_id,
            text=text or "❤️",
        )

    await deactivate_reminder(r_id)

    await message.answer(
        f"Случайное напоминание (ID {r_id}) отправлено девушке 💌\n"
        f"И помечено как использованное."
    )


# --- /reset + кнопка 'Активировать все' ---


@router.message(Command("reset"))
@router.message(F.text == ADMIN_BTN_RESET)
async def reset_handler(message: Message):
    # """
    # /reset — делает все напоминания снова активными (только админ).
    # """
    if not is_admin(message):
        return await message.answer("Эта команда только для админа 😇")

    count = await activate_all_reminders()
    await message.answer(
        f"Готово ✅\n"
        f"Активировал(а) {count} напоминаний.\n\n"
        f"Теперь бот снова может отправлять все сохранённые тексты и фотки 💌"
    )


# --- /wishes + кнопка 'Хотелки' ---


@router.message(Command("wishes"))
@router.message(F.text == ADMIN_BTN_WISHES)
async def wishes_list_handler(message: Message):
    # """
    # Показывает список хотелок девушки (только админ).
    # """
    if not is_admin(message):
        return await message.answer("Эта команда только для админа 😇")

    wishes = await list_wishes(limit=20)
    if not wishes:
        return await message.answer("Пока нет ни одной хотелки 💭")

    lines = []
    for w_id, user_id, text, photo_file_id, status, created_at in wishes:
        if photo_file_id and text:
            kind = "🖼+📝"
        elif photo_file_id:
            kind = "🖼"
        else:
            kind = "📝"

        short_text = text or "(без текста)"
        if len(short_text) > 40:
            short_text = short_text[:37] + "..."

        lines.append(f"#{w_id} [{status}] {kind} {short_text} ({created_at})")

    await message.answer("Список хотелок:\n\n" + "\n".join(lines))
