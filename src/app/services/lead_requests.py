from aiomax import Message, User
from aiomax.fsm import FSMCursor

from app.bitrix import BitrixClient
from app.catalog import ITEMS_BY_KEY
from app.max.const import ADDITIONAL_SERVICE_LABELS
from app.max.states import get_state_data
from app.types import RequestContext, RequestLeadSubmission


class LeadRequestService:
    @staticmethod
    def max_user_label(user: User | None) -> str:
        if user is None:
            return "unknown"

        username = f"@{user.username}" if user.username else "-"
        return f"{user.name} ({username})"

    @staticmethod
    def build_request_context(target: str, event_details: str | None) -> RequestContext:
        if target == "event":
            return RequestContext(
                item_title="Мероприятие",
                category="Мероприятие",
                event_details=event_details,
            )

        if target == "corporate":
            return RequestContext(
                item_title="Корпоратив",
                category="Мероприятие",
                event_details=event_details,
            )

        item = ITEMS_BY_KEY[target]
        return RequestContext(
            item_title=item.title,
            category=item.category_label,
            event_details=event_details,
        )

    @staticmethod
    async def build_submission(
        *,
        message: Message,
        cursor: FSMCursor,
        phone: str,
    ) -> RequestLeadSubmission:
        data = get_state_data(cursor)
        target = str(data["target"])
        name = str(data["name"])
        people_count_raw = data.get("people_count")
        people_count = str(people_count_raw) if isinstance(people_count_raw, str) else None
        age_raw = data.get("age")
        age = str(age_raw) if isinstance(age_raw, str) else None
        comment_raw = data.get("comment")
        comment = str(comment_raw) if isinstance(comment_raw, str) else None
        booking_datetime_raw = data.get("booking_datetime")
        booking_datetime = str(booking_datetime_raw) if isinstance(booking_datetime_raw, str) else None
        selected_additional_services_keys = tuple(
            str(value) for value in data.get("selected_additional_services", []) if isinstance(value, str)
        )
        selected_additional_services = tuple(
            ADDITIONAL_SERVICE_LABELS[key]
            for key in selected_additional_services_keys
            if key in ADDITIONAL_SERVICE_LABELS
        )
        event_details_raw = data.get("event_details")
        event_details = str(event_details_raw) if isinstance(event_details_raw, str) else None
        selection_path = tuple(str(value) for value in data.get("selection_path", []) if isinstance(value, str))
        request_context = LeadRequestService.build_request_context(target, event_details)
        requester_label_raw = data.get("requester_label")
        requester_label = (
            str(requester_label_raw)
            if isinstance(requester_label_raw, str)
            else LeadRequestService.max_user_label(message.sender)
        )
        requester_id_raw = data.get("requester_id")
        requester_id = (
            int(requester_id_raw)
            if isinstance(requester_id_raw, int)
            else (message.sender.user_id if message.sender is not None else 0)
        )

        if not selection_path:
            selection_path = (request_context.category, request_context.item_title)

        comments = BitrixClient.build_comments(
            category=request_context.category,
            item_title=request_context.item_title,
            max_user=requester_label,
            max_id=requester_id,
            event_details=request_context.event_details,
            selected_options=list(selection_path),
            people_count=people_count,
            age=age,
            comment=comment,
            booking_datetime=booking_datetime,
            selected_additional_services=list(selected_additional_services),
        )

        return RequestLeadSubmission(
            target=target,
            name=name,
            phone=phone,
            title=f"Заявка из Max: {request_context.item_title}",
            item_title=request_context.item_title,
            category=request_context.category,
            selection_path=selection_path,
            comments=comments,
            people_count=people_count,
            age=age,
            comment=comment,
            booking_datetime=booking_datetime,
            selected_additional_services=selected_additional_services,
            event_details=request_context.event_details,
        )

    @staticmethod
    def build_preview_text(submission: RequestLeadSubmission) -> str:
        lines = [
            "<b>Проверьте, пожалуйста, вашу заявку</b>",
            "",
            f"Вас интересует: {submission.item_title}",
            f"Как к вам обращаться: {submission.name}",
            f"Ваш телефон: {submission.phone}",
        ]

        if submission.selection_path:
            lines.append(f"Вы выбрали: {' -> '.join(submission.selection_path)}")

        if submission.selected_additional_services:
            lines.append(f"Дополнительно для вас: {', '.join(submission.selected_additional_services)}")

        if submission.people_count:
            lines.append(f"Количество гостей: {submission.people_count}")

        if submission.age:
            lines.append(f"Возраст участников: {submission.age}")

        if submission.booking_datetime:
            lines.append(f"Дата и время брони: {submission.booking_datetime}")

        if submission.event_details:
            lines.append(f"Что вы планируете: {submission.event_details}")

        if submission.comment:
            lines.append(f"Ваши пожелания: {submission.comment}")

        lines.extend(
            [
                "",
                "Если все верно, отправьте заявку. Если хотите что-то изменить, заполните ее заново или вернитесь в главное меню.",
            ]
        )
        return "\n".join(lines)

    @staticmethod
    async def submit_lead_request(
        *,
        bitrix: BitrixClient,
        submission: RequestLeadSubmission,
    ) -> None:
        lead_id = await bitrix.find_lead_by_phone(submission.phone)

        if lead_id is None:
            await bitrix.create_lead(
                name=submission.name,
                phone=submission.phone,
                title=submission.title,
                comments=submission.comments,
            )
            return

        await bitrix.update_lead_context(
            lead_id,
            title=submission.title,
            name=submission.name,
            comments=submission.comments,
        )
