from aiomax import Callback, Message, Router, filters
from aiomax.fsm import FSMCursor
from loguru import logger

from app.bitrix import BitrixAPIError
from app.catalog import RENT_SPACES, RENT_STAY
from app.services.helper import HandlersHelper
from app.services.lead_requests import LeadRequestService
from app.max.const import CORPORATE_GROUP_LABELS
from app.max.keyboards import (
    comment_skip_keyboard,
    main_menu_keyboard,
    phone_keyboard,
    request_confirmation_keyboard,
    request_people_count_keyboard,
)
from app.max.platform import get_bitrix
from app.max.states import (
    RequestLeadState,
    clear_context,
    get_state_data,
    set_state,
    update_state_data,
)

router = Router()
RENT_TARGETS = {item.key for item in (*RENT_STAY, *RENT_SPACES)}


def has_contact_attachment(message: Message) -> bool:
    attachments = message.body.attachments or []
    return any(getattr(attachment, "type", None) == "contact" for attachment in attachments)


def extract_contact_phone(message: Message) -> str | None:
    attachments = message.body.attachments or []
    for attachment in attachments:
        if getattr(attachment, "type", None) != "contact":
            continue
        phone = getattr(attachment, "vcf_phone", None)
        if isinstance(phone, str) and phone.strip():
            return phone.strip()
    return None


def is_request_size_callback(callback: Callback) -> bool:
    payload = callback.payload or ""
    return payload.startswith("request:size:")


def is_request_start_callback(callback: Callback) -> bool:
    payload = callback.payload or ""
    return (
        payload.startswith("request:")
        and not payload.startswith("request:size:")
        and payload not in {"request:skip_comment", "request:submit", "request:restart"}
    )


async def request_age_or_comment(message: Message, cursor: FSMCursor) -> None:
    target_raw = get_state_data(cursor).get("target")
    target = str(target_raw) if isinstance(target_raw, str) else ""

    if target in RENT_TARGETS:
        update_state_data(cursor, age=None)
        set_state(cursor, RequestLeadState.waiting_for_comment)
        await message.send(
            "Если у вас есть пожелания, напишите их следующим сообщением. Если комментарий не нужен, нажмите «Пропустить».",
            keyboard=comment_skip_keyboard(),
        )
        return

    set_state(cursor, RequestLeadState.waiting_for_age)
    await message.send("Подскажите, пожалуйста, возраст участников. Если возраст разный, можно написать диапазон.")


@router.on_button_callback("request:skip_comment", filters.state(RequestLeadState.waiting_for_comment))
async def skip_comment(callback: Callback, cursor: FSMCursor) -> None:
    message = HandlersHelper.callback_message(callback)
    if message is None:
        return

    update_state_data(cursor, comment=None)
    set_state(cursor, RequestLeadState.waiting_for_booking_datetime)
    await message.send("Подскажите, пожалуйста, на какую дату и время вы хотите бронь. Например: 12.04 в 18:00.")
    await callback.answer(notification="Комментарий пропущен")


@router.on_button_callback("request:submit", filters.state(RequestLeadState.waiting_for_confirmation))
async def confirm_request_submission(callback: Callback, cursor: FSMCursor) -> None:
    message = HandlersHelper.callback_message(callback)
    if message is None:
        return

    data = get_state_data(cursor)
    phone = data.get("phone")
    if not isinstance(phone, str) or not phone:
        await callback.answer(notification="Не удалось найти ваш телефон для отправки")
        return

    submission = await LeadRequestService.build_submission(message=message, cursor=cursor, phone=phone)
    logger.info(
        "Submitting lead: target={target}, title={title}, name={name}, phone={phone}, people_count={people_count}, age={age}, booking_datetime={booking_datetime}, additional_services={additional_services}, selection_path={selection_path}, comment={comment}, event_details={event_details}",
        target=submission.target,
        title=submission.title,
        name=submission.name,
        phone=submission.phone,
        people_count=submission.people_count,
        age=submission.age,
        booking_datetime=submission.booking_datetime,
        additional_services=", ".join(submission.selected_additional_services),
        selection_path=" -> ".join(submission.selection_path),
        comment=submission.comment,
        event_details=submission.event_details,
    )
    logger.info("Lead comments payload:\n{comments}", comments=submission.comments)

    try:
        await LeadRequestService.submit_lead_request(
            bitrix=get_bitrix(callback),
            submission=submission,
        )
    except BitrixAPIError as exc:
        logger.exception("Bitrix API error")
        await message.send(f"Не получилось отправить вашу заявку в Bitrix24: {exc}")
        await callback.answer(notification="Не удалось отправить заявку")
        return
    except Exception:
        logger.exception("Unexpected error during lead submission")
        await message.send("Не получилось отправить вашу заявку. Попробуйте, пожалуйста, еще раз чуть позже.")
        await callback.answer(notification="Не удалось отправить заявку")
        return

    clear_context(cursor)
    await callback.answer(notification="Ваша заявка отправлена")
    await message.send("Спасибо, ваша заявка отправлена. Мы свяжемся с вами после обработки.")
    await message.send(
        "Выберите, что вас интересует, а я помогу сориентироваться и оставить заявку.",
        keyboard=main_menu_keyboard(),
    )


@router.on_button_callback("request:restart", filters.state(RequestLeadState.waiting_for_confirmation))
async def restart_request(callback: Callback, cursor: FSMCursor) -> None:
    message = HandlersHelper.callback_message(callback)
    if message is None:
        return

    data = get_state_data(cursor)
    target = data.get("target")
    selection_path = [str(value) for value in data.get("selection_path", []) if isinstance(value, str)]
    corporate_group_label = data.get("corporate_group_label")
    selected_additional_services = [
        str(value) for value in data.get("selected_additional_services", []) if isinstance(value, str)
    ]

    if not isinstance(target, str) or not target:
        await callback.answer(notification="Не получилось начать заполнение заново")
        return

    await callback.answer(notification="Заполняем заново")
    await HandlersHelper.start_request_flow(
        message=message,
        cursor=cursor,
        target=target,
        selection_path=selection_path,
        corporate_group_label=corporate_group_label if isinstance(corporate_group_label, str) else None,
        requester_label=LeadRequestService.max_user_label(callback.user),
        requester_id=callback.user.user_id,
        selected_additional_services=selected_additional_services,
    )


@router.on_button_callback(is_request_size_callback, filters.state(RequestLeadState.waiting_for_people_count))
async def request_people_count_selected(callback: Callback, cursor: FSMCursor) -> None:
    message = HandlersHelper.callback_message(callback)
    data = callback.payload
    if message is None or data is None:
        return

    group_key = data.split(":", 2)[2]
    group_label = CORPORATE_GROUP_LABELS.get(group_key)
    if group_label is None:
        await callback.answer(notification="Не удалось определить количество гостей")
        return

    update_state_data(cursor, people_count=group_label)
    await request_age_or_comment(message, cursor)
    await callback.answer(notification=f"Вы выбрали: {group_label}")


@router.on_button_callback(is_request_start_callback)
async def start_request(callback: Callback, cursor: FSMCursor) -> None:
    message = HandlersHelper.callback_message(callback)
    data = callback.payload
    if message is None or data is None:
        return

    target = data.split(":", 1)[1]
    existing_data = get_state_data(cursor)
    selection_path = [str(value) for value in existing_data.get("selection_path", []) if isinstance(value, str)]
    corporate_group_label = existing_data.get("corporate_group_label")
    selected_additional_services = [
        str(value) for value in existing_data.get("selected_additional_services", []) if isinstance(value, str)
    ]

    await HandlersHelper.start_request_flow(
        message=message,
        cursor=cursor,
        target=target,
        selection_path=selection_path,
        corporate_group_label=corporate_group_label if isinstance(corporate_group_label, str) else None,
        requester_label=LeadRequestService.max_user_label(callback.user),
        requester_id=callback.user.user_id,
        selected_additional_services=selected_additional_services,
    )


@router.on_message(filters.state(RequestLeadState.waiting_for_event_details))
async def process_event_details(message: Message, cursor: FSMCursor) -> None:
    details = (message.content or "").strip()
    if not details:
        await message.send("Пожалуйста, опишите ваше мероприятие одним сообщением.")
        return

    update_state_data(cursor, event_details=details)
    set_state(cursor, RequestLeadState.waiting_for_name)
    await message.send("Подскажите, пожалуйста, как к вам обращаться?")


@router.on_message(filters.state(RequestLeadState.waiting_for_name))
async def process_name(message: Message, cursor: FSMCursor) -> None:
    name = (message.content or "").strip()
    if not name:
        await message.send("Пожалуйста, напишите, как к вам обращаться.")
        return

    update_state_data(cursor, name=name)

    data = get_state_data(cursor)
    people_count = data.get("people_count")
    if isinstance(people_count, str) and people_count:
        await request_age_or_comment(message, cursor)
        return

    set_state(cursor, RequestLeadState.waiting_for_people_count)
    await message.send(
        "Сколько человек планируется? Выберите, пожалуйста, подходящий вариант кнопкой ниже.",
        keyboard=request_people_count_keyboard(),
    )


@router.on_message(filters.state(RequestLeadState.waiting_for_people_count))
async def process_people_count(message: Message) -> None:
    await message.send(
        "Пожалуйста, выберите количество гостей кнопкой ниже.",
        keyboard=request_people_count_keyboard(),
    )


@router.on_message(filters.state(RequestLeadState.waiting_for_age))
async def process_age(message: Message, cursor: FSMCursor) -> None:
    age = (message.content or "").strip()
    if not age:
        await message.send("Пожалуйста, укажите возраст участников или возрастной диапазон.")
        return

    update_state_data(cursor, age=age)
    set_state(cursor, RequestLeadState.waiting_for_comment)
    await message.send(
        "Если у вас есть пожелания, напишите их следующим сообщением. Если комментарий не нужен, нажмите «Пропустить».",
        keyboard=comment_skip_keyboard(),
    )


@router.on_message(filters.state(RequestLeadState.waiting_for_comment))
async def process_comment(message: Message, cursor: FSMCursor) -> None:
    comment = (message.content or "").strip()
    if not comment:
        await message.send("Напишите, пожалуйста, ваши пожелания сообщением или нажмите «Пропустить».")
        return

    if comment.lower() in {"пропустить", "skip", "-"}:
        update_state_data(cursor, comment=None)
        set_state(cursor, RequestLeadState.waiting_for_booking_datetime)
        await message.send("Подскажите, пожалуйста, на какую дату и время вы хотите бронь. Например: 12.04 в 18:00.")
        return

    update_state_data(cursor, comment=comment)
    set_state(cursor, RequestLeadState.waiting_for_booking_datetime)
    await message.send("Подскажите, пожалуйста, на какую дату и время вы хотите бронь. Например: 12.04 в 18:00.")


@router.on_message(filters.state(RequestLeadState.waiting_for_booking_datetime))
async def process_booking_datetime(message: Message, cursor: FSMCursor) -> None:
    booking_datetime = (message.content or "").strip()
    if not booking_datetime:
        await message.send("Пожалуйста, напишите дату и время брони одним сообщением.")
        return

    update_state_data(cursor, booking_datetime=booking_datetime)
    set_state(cursor, RequestLeadState.waiting_for_phone)
    await message.send(
        "Теперь отправьте, пожалуйста, ваш номер телефона. Можно нажать кнопку ниже или написать его сообщением.",
        keyboard=phone_keyboard(),
    )


@router.on_message(filters.state(RequestLeadState.waiting_for_phone), has_contact_attachment)
async def process_phone_contact(message: Message, cursor: FSMCursor) -> None:
    phone = extract_contact_phone(message)
    if phone is None:
        await message.send("Не получилось получить ваш контакт. Пожалуйста, отправьте номер телефона сообщением.")
        return

    await HandlersHelper.show_preview(message, cursor, phone)


@router.on_message(filters.state(RequestLeadState.waiting_for_phone), lambda message: not has_contact_attachment(message))
async def process_phone_text(message: Message, cursor: FSMCursor) -> None:
    phone = (message.content or "").strip()
    if len(phone) < 6:
        await message.send("Похоже, номер слишком короткий. Пожалуйста, отправьте корректный телефон.")
        return

    await HandlersHelper.show_preview(message, cursor, phone)


@router.on_message(filters.state(RequestLeadState.waiting_for_confirmation))
async def process_confirmation_text(message: Message) -> None:
    await message.send(
        "Пожалуйста, проверьте данные в предпросмотре и выберите действие кнопкой ниже.",
        keyboard=request_confirmation_keyboard(),
    )
