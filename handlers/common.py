from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from keyboards import get_admin_keyboard


from config import ADMIN_ID
from db import get_girlfriend_chat_id, set_girlfriend_chat_id

# Роутер для общих команд
router = Router()


@router.message(Command("start"))
async def start_handler(message: Message):
    # """
    # Обрабатывает команду /start.

    # Если это админ — показывает служебное сообщение.
    # Если это не админ:
    #   - если chat_id девушки ещё не сохранён — сохраняет его как chat_id получателя,
    #   - если уже сохранён — просто приветствует.
    # """
    user_id = message.from_user.id if message.from_user else None

    # Случай: админ
    if user_id == ADMIN_ID:
        await message.answer(
            "Привет, админ! 👨‍💻\n\n"
            "Я готов отправлять напоминания.\n"
            "Команды:\n"
            "/add — добавить напоминание\n"
            "/list — список напоминаний\n"
            "/delete ID — отключить напоминание\n"
            "/send_random — отправить случайное напоминание девушке\n"
            "/reset - снова активировать все напоминания",
            reply_markup=get_admin_keyboard()
        )
        return

    # Случай: не админ — потенциально твоя девушка
    girlfriend_chat_id = await get_girlfriend_chat_id()

    if girlfriend_chat_id is None:
        # Первый раз кто-то написал боту — считаем, что это она
        await set_girlfriend_chat_id(message.chat.id)
        await message.answer(
            "Привет! 🥰\n\n"
            "Я небольшой бот, которого Серёжа сделал специально для тебя.\n"
            "Иногда я буду присылать тебе тёплые напоминания, как сильно он тебя любит 💌"
        )
    else:
        # chat_id уже сохранён — просто приветствуем
        await message.answer(
            "Рад тебя снова видеть! 💖\n"
            "Я — бот-напоминалка от Серёжи 🫶"
        )


@router.message(Command("whoami"))
async def whoami_handler(message: Message):
    """Обрабатывает команду /whoami — показывает ID пользователя."""
    await message.answer(
        f"Твой Telegram ID: `{message.from_user.id}`",
        parse_mode="Markdown"
    )
