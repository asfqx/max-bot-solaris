import asyncio

from aiomax import Bot
from loguru import logger

from app.bitrix import BitrixClient
from app.core.db import engine
from app.core.settings import settings
from app.services.reminder import ReminderService
from app.max import setup_routers


async def main() -> None:
    logger.info(
        "Starting Max bot with Bitrix source_id={source_id}, lead_status_id={lead_status_id}, webhook={webhook}",
        source_id=settings.bitrix_source_id,
        lead_status_id=settings.bitrix_lead_status_id,
        webhook=settings.bitrix_webhook_url,
    )

    bot = Bot(
        access_token=settings.bot_token,
        default_format="html",
    )
    setup_routers(bot)
    weekly_reminder = ReminderService()

    async with BitrixClient(
        webhook_url=settings.bitrix_webhook_url,
        source_id=settings.bitrix_source_id,
        assigned_by_id=settings.bitrix_assigned_by_id,
        lead_status_id=settings.bitrix_lead_status_id,
    ) as bitrix:
        setattr(bot, "bitrix", bitrix)
        setattr(bot, "weekly_reminder", weekly_reminder)
        reminder_task = asyncio.create_task(weekly_reminder.run(bot))

        try:
            await bot.start_polling()
        finally:
            reminder_task.cancel()
            await asyncio.gather(reminder_task, return_exceptions=True)
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
