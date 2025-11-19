import asyncio

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from db import (
    init_db,
    get_girlfriend_chat_id,
    get_random_active_reminder,
    deactivate_reminder
)
from handlers import register_handlers

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz


async def send_daily_reminder(bot: Bot):
    # """
    # Отправляет один случайный активный ремайндер девушке.
    # Вызывается планировщиком каждый день в 10:00.
    # """
    girlfriend_chat_id = await get_girlfriend_chat_id()
    if girlfriend_chat_id is None:
        # Девушка ещё не писала боту /start — просто выходим тихо
        print("[scheduler] Нет chat_id девушки, напоминание не отправлено")
        return

    reminder = await get_random_active_reminder()
    if reminder is None:
        # Нет активных напоминаний
        print("[scheduler] Нет активных напоминаний, отправлять нечего")
        return

    r_id, text, photo_file_id = reminder

    # Отправляем либо фото+текст, либо просто текст
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
    # Деавктивирует отправленное напоминание
    await deactivate_reminder(r_id)

    print(f"[scheduler] Отправлено запланированное напоминание ID={r_id}")


async def main():
    # """
    # Инициализирует БД, настраивает бота, регистрирует хэндлеры,
    # поднимает планировщик и запускает long polling.
    # """
    # Инициализируем базу
    await init_db()

    # Создаём бота и диспетчер
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Регистрируем хэндлеры
    register_handlers(dp)

    # Таймзона для расписания — Europe/Helsinki
    helsinki_tz = pytz.timezone("Europe/Helsinki")

    # Настраиваем планировщик
    scheduler = AsyncIOScheduler(timezone=helsinki_tz)

    # каждый день в 11:00 по Хельсинки
    scheduler.add_job(
        send_daily_reminder,
        trigger=CronTrigger(hour=11, minute=0),
        args=(bot,),
        name="daily_love_reminder",
    )

    # Запускаем планировщик
    scheduler.start()
    print("Планировщик запущен: ежедневное напоминание в 10:00")

    print("Бот запущен...")
    # Запускаем обработку апдейтов
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

