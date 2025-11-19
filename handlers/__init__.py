from aiogram import Dispatcher

from .common import router as common_router
from .admin import router as admin_router


def register_handlers(dp: Dispatcher):
    # """Регистрирует все роутеры (группы хэндлеров) в диспетчере."""
    dp.include_router(common_router)
    dp.include_router(admin_router)