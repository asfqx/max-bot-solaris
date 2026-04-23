import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID

from aiomax import Bot, exceptions as aiomax_exceptions
from loguru import logger

from app.constants import REMINDER_MESSAGES
from app.core import AsyncSessionLocal
from app.max.keyboards import main_menu_keyboard
from app.users import User, UserRepository


class ReminderService:
    def __init__(
        self,
        *,
        reminder_interval: timedelta = timedelta(days=3),
        poll_interval_seconds: int = 3600,
    ) -> None:
        self._reminder_interval = reminder_interval
        self._poll_interval_seconds = poll_interval_seconds

    async def subscribe_chat(
        self,
        *,
        chat_id: int,
        username: str | None,
        full_name: str | None,
    ) -> None:
        next_reminder_at = datetime.now(timezone.utc) + self._reminder_interval

        async with AsyncSessionLocal() as session:
            user = await UserRepository.get_by_chat_id(chat_id=chat_id, session=session)

            if not user:
                user = User(
                    chat_id=chat_id,
                    username=username,
                    full_name=full_name,
                    next_reminder_at=next_reminder_at,
                )
                await UserRepository.add(user=user, session=session)
            else:
                user.username = username
                user.full_name = full_name
                user.next_reminder_at = next_reminder_at

                await session.commit()

    async def unsubscribe_chat(self, chat_id: int) -> bool:
        async with AsyncSessionLocal() as session:
            user = await UserRepository.get_by_chat_id(session=session, chat_id=chat_id)

            if user is None:
                return False

            await UserRepository.delete(session=session, user=user)

            return True

    async def run(self, bot: Bot) -> None:
        logger.info("Weekly reminder loop started")
        try:
            while True:
                try:
                    await self.send_due_reminders(bot)
                except Exception:
                    logger.exception("Weekly reminder iteration failed")

                await asyncio.sleep(self._poll_interval_seconds)
        except asyncio.CancelledError:
            logger.info("Weekly reminder loop stopped")
            raise

    async def send_due_reminders(self, bot: Bot) -> None:
        async with AsyncSessionLocal() as session:
            recipients = await UserRepository.list_due(session=session, due_before=datetime.now(timezone.utc))

        for recipient in recipients:
            reminder_index = (recipient.last_reminder_index + 1) % len(REMINDER_MESSAGES)
            reminder_text = REMINDER_MESSAGES[reminder_index]

            try:
                await bot.send_message(
                    text=reminder_text,
                    chat_id=recipient.chat_id,
                    keyboard=main_menu_keyboard(),
                )
            except (
                aiomax_exceptions.AccessDeniedException,
                aiomax_exceptions.ChatNotFound,
                aiomax_exceptions.NotFoundException,
            ) as exc:
                logger.info(
                    "Removing chat {chat_id} from reminders after Max error: {error}",
                    chat_id=recipient.chat_id,
                    error=self._exception_text(exc),
                )
                await self._delete_recipient(user_uuid=recipient.uuid)
                continue
            except aiomax_exceptions.AiomaxException as exc:
                error_text = self._exception_text(exc).lower()
                if "chat not found" in error_text or "access denied" in error_text:
                    logger.info(
                        "Removing chat {chat_id} from reminders after Max error: {error}",
                        chat_id=recipient.chat_id,
                        error=error_text,
                    )
                    await self._delete_recipient(user_uuid=recipient.uuid)
                    continue
                raise

            reminded_at = datetime.now(timezone.utc)
            next_reminder_at = reminded_at + self._reminder_interval

            async with AsyncSessionLocal() as session:
                user = await UserRepository.get_by_uuid(session=session, user_uuid=recipient.uuid)

                if not user:
                    continue

                user.last_reminder_sent_at = reminded_at
                user.next_reminder_at = next_reminder_at
                user.last_reminder_index = reminder_index

                await session.commit()

    async def _delete_recipient(self, *, user_uuid: UUID) -> None:
        async with AsyncSessionLocal() as session:
            user = await UserRepository.get_by_uuid(session=session, user_uuid=user_uuid)

            if not user:
                return

            await UserRepository.delete(session=session, user=user)

    @staticmethod
    def _exception_text(exc: Exception) -> str:
        details = [
            getattr(exc, "text", None),
            getattr(exc, "description", None),
            str(exc),
        ]
        return " ".join(part for part in details if part)
