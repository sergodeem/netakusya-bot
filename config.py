from dotenv import load_dotenv
import os

# Загружаем переменные окружения из файла .env
load_dotenv()

# Токен бота из .env
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ID администратора , тоже берем из .env
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))