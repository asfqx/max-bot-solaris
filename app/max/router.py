from aiomax import Bot

from app.max.handlers.menu import router as menu_router
from app.max.handlers.requests import router as requests_router


def setup_routers(bot: Bot) -> None:
    bot.add_router(menu_router)
    bot.add_router(requests_router)
