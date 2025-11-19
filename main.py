import asyncio

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramNetworkError


from config import BOT_TOKEN
from db import (
    init_db,
    get_girlfriend_chat_id,
    get_random_active_reminder,
    deactivate_reminder,
    is_wishes_feature_notified,
    set_wishes_feature_notified,

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



async def notify_about_wishes_feature(bot: Bot):
    # """
    # Один раз отправляет девушке сообщение о новой функции 'хотелки'.
    # Больше не шлёт, если в app_state стоит флаг wishes_feature_notified = 1.
    # """
    # Уже уведомляли? Тогда выходим.
    if await is_wishes_feature_notified():
        return

    girlfriend_chat_id = await get_girlfriend_chat_id()
    if girlfriend_chat_id is None:
        # Ещё не знаем, кто девушка — некого уведомлять.
        return

    text = (
        "Привет!✨\n\n"
        "У меня появилась новая функция — теперь сюда можно отправлять свои хотелки 💭\n"
        "Что угодно, что тебе хочется, нравится или о чём ты мечтаешь.\n\n"
        "Это может быть:\n"
        "• Место, куда ты хочешь сходить 🌆\n"
        "• Идея для прогулки или свидания 🌿\n"
        "• Подарок, который тебе понравился 🎀\n"
        "• Ссылка на то, что ты бы хотела посмотреть или купить 🛍\n"
        "• Скриншот, фото или текст с любым желанием 📸\n"
        "• Идея полезного для тебя функционала у этого бота🥷\n"
        "• Какая-то мысль, идея, настроение или маленькая мечта ✨\n\n"
        "Как это работает:\n"
        "1. Нажми кнопку «Хочу» снизу.\n"
        "2. Напиши, что именно ты хочешь — можно с фото, ссылкой или просто текстом.\n"
        "3. Я всё сохраню и передам Серёже ❤️\n"
        "   А он обязательно это увидит и когда-нибудь воплотит 😉\n\n"
        "Можешь попробовать прямо сейчас!"
    )

    await bot.send_message(chat_id=girlfriend_chat_id, text=text)

    # Помечаем, что уведомление отправлено
    await set_wishes_feature_notified()



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
    
    # 👉 безопасно пытаемся отправить уведомление о новой фиче
    try:
        await notify_about_wishes_feature(bot)
    except TelegramNetworkError as e:
        print(f"[notify] Не удалось отправить уведомление о новой функции: {e}")


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

