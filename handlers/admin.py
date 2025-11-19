from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import Command
from keyboards import ADMIN_BTN_SEND, ADMIN_BTN_LIST, ADMIN_BTN_RESET


from config import ADMIN_ID
from db import (
    add_reminder,
    list_reminders,
    deactivate_reminder,
    get_girlfriend_chat_id,
    get_random_active_reminder,
    activate_all_reminders,
)

# Роутер для админских команд
router = Router()


def is_admin(message: Message) -> bool:
    # """Проверяет, является ли пользователь админом по его Telegram ID."""
    return message.from_user and message.from_user.id == ADMIN_ID


@router.message(Command("add"))
async def add_handler(message: Message):
    # """
    # Обрабатывает команду /add — добавляет напоминание (только для админа).

    # Работает в двух вариантах:
    # 1) Текстовое сообщение:
    #    /add я тебя люблю ❤️

    # 2) Фото с подписью:
    #    (фото) + подпись: /add я тебя люблю ❤️
    #    → сохранится и текст, и фото.
    # """
    if not is_admin(message):
        return await message.answer("Эта команда только для админа 😇")

    # Команда /add может быть в message.text (обычный текст)
    # или в message.caption (подпись к фото/видео)
    raw = message.text or message.caption
    if not raw:
        return await message.answer(
            "Использование: `/add текст напоминания`\n"
            "Можно отправить просто текст или фото с подписью.",
            parse_mode="Markdown"
        )

    parts = raw.split(" ", 1)
    if len(parts) < 2 or not parts[1].strip():
        return await message.answer(
            "После команды нужно написать текст.\n\n"
            "Пример:\n`/add ты самая лучшая на свете 💖`",
            parse_mode="Markdown"
        )

    text = parts[1].strip()

    # Если вместе с /add прилетело фото — сохраняем ещё и photo_file_id
    photo_file_id = None
    if message.photo:
        # Берём самое большое фото (последний элемент массива)
        largest_photo = message.photo[-1]
        photo_file_id = largest_photo.file_id

    reminder_id = await add_reminder(text=text, photo_file_id=photo_file_id)

    description = []
    if text:
        description.append("📝 текст")
    if photo_file_id:
        description.append("🖼 фото")

    description_str = " + ".join(description) if description else "пустое напоминание"

    await message.answer(
        f"Напоминание сохранено ✅\n"
        f"ID: {reminder_id}\n"
        f"Состав: {description_str}"
    )


@router.message(Command("list"))
@router.message(F.text == ADMIN_BTN_LIST)
async def list_handler(message: Message):
    # """Обрабатывает команду /list — показывает список всех напоминаний (только для админа)."""
    if not is_admin(message):
        return await message.answer("Эта команда только для админа 😇")

    reminders = await list_reminders()
    if not reminders:
        return await message.answer("Пока нет ни одного напоминания.")

    lines = []
    for r_id, text, photo_file_id, is_active in reminders:
        status = "✅" if is_active else "🚫"

        # Отмечаем, что это за тип напоминания
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


@router.message(Command("delete"))
async def delete_handler(message: Message):
    # """Обрабатывает команду /delete — помечает напоминание как неактивное по ID (только для админа)."""
    if not is_admin(message):
        return await message.answer("Эта команда только для админа 😇")

    raw = message.text or message.caption
    parts = raw.split(" ", 1) if raw else []
    if len(parts) < 2 or not parts[1].strip():
        return await message.answer(
            "Использование: `/delete ID`\nПример: `/delete 1`",
            parse_mode="Markdown"
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


@router.message(Command("send_random"))
@router.message(F.text == ADMIN_BTN_SEND)
async def send_random_handler(message: Message, bot: Bot):
    # """
    # Обрабатывает команду /send_random — отправляет девушке случайное активное напоминание.

    # Если:
    #   - девушка ещё не написала боту — просит её написать /start,
    #   - нет активных напоминаний — просит их добавить.
    # """
    if not is_admin(message):
        return await message.answer("Эта команда только для Господина😇")

    # Получаем chat_id девушки
    girlfriend_chat_id = await get_girlfriend_chat_id()
    if girlfriend_chat_id is None:
        return await message.answer(
            "Я ещё не знаю chat_id девушки 🥺\n"
            "Пусть она напишет этому боту команду /start хотя бы один раз."
        )

    # Берём случайное активное напоминание
    reminder = await get_random_active_reminder()
    if reminder is None:
        return await message.answer(
            "Нет активных напоминаний 😢\n"
            "Добавь хотя бы одно через `/add`.",
            parse_mode="Markdown"
        )

    r_id, text, photo_file_id = reminder

    # Отправляем ей фото+текст или просто текст
    if photo_file_id:
        await bot.send_photo(
            chat_id=girlfriend_chat_id,
            photo=photo_file_id,
            caption=text or None
        )
    else:
        await bot.send_message(
            chat_id=girlfriend_chat_id,
            text=text or "❤️"
        )
    # Деактивируем отправленное напоминание
    await deactivate_reminder(r_id)

    await message.answer(f"Случайное напоминание (ID {r_id}) отправлено девушке 💌")

@router.message(Command("reset"))
@router.message(F.text == ADMIN_BTN_RESET)
async def reset_handler(message: Message):
    # """
    # Обрабатывает команду /reset — делает все напоминания снова активными (только для админа).
    # """
    if not is_admin(message):
        return await message.answer("Эта команда только для админа 😇")

    count = await activate_all_reminders()

    await message.answer(
        f"Готово ✅\n"
        f"Активировал(а) {count} напоминаний.\n\n"
        f"Теперь бот снова может отправлять все сохранённые тексты и фотки 💌"
    )
