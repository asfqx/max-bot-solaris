from typing import TYPE_CHECKING, Any, cast

from aiomax import Bot

if TYPE_CHECKING:
    from app.bitrix import BitrixClient
    from app.services.reminder import ReminderService


def bot_from_context(context: Any) -> Bot:
    if isinstance(context, Bot):
        return context

    bot = getattr(context, "bot", None)
    if isinstance(bot, Bot):
        return bot

    raise RuntimeError("Bot instance is not available in the current context.")


def get_service(context: Any, attribute: str) -> Any:
    bot = bot_from_context(context)
    service = getattr(bot, attribute, None)
    if service is None:
        raise RuntimeError(f"{attribute} service is not configured on the bot.")
    return service


def get_bitrix(context: Any) -> "BitrixClient":
    return cast("BitrixClient", get_service(context, "bitrix"))


def get_weekly_reminder(context: Any) -> "ReminderService":
    return cast("ReminderService", get_service(context, "weekly_reminder"))
