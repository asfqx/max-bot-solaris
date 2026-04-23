from typing import Any

from aiomax import BotStartPayload, Callback, CommandContext, Router
from aiomax.fsm import FSMCursor

from app.catalog import (
    CORPORATE_CATERING_INFO,
    CORPORATE_INFO,
    CORPORATE_MENU_FILE_PATH,
    EVENT_INFO,
    ITEMS_BY_KEY,
    KARTING_FAQ,
    ROUTE_TEXT,
    SUPPORT_PHONE,
)
from app.services.helper import HandlersHelper
from app.max.const import (
    ADDITIONAL_SERVICE_LABELS,
    CORPORATE_ACTIVITY_LABELS,
    CORPORATE_GROUP_LABELS,
    EXTRAS_SOURCE_CONFIG,
    RENT_SPACE_GROUP_LABELS,
)
from app.max.keyboards import (
    about_club_back_keyboard,
    about_club_keyboard,
    activities_keyboard,
    corporate_group_keyboard,
    karting_info_keyboard,
    main_menu_keyboard,
    rent_keyboard,
    rent_spaces_group_keyboard,
    rent_spaces_keyboard,
    rent_stay_keyboard,
    request_button,
    route_keyboard,
)
from app.max.platform import get_weekly_reminder
from app.max.states import clear_context, get_state_data, update_state_data

router = Router()


@router.on_bot_start()
async def bot_started(payload: BotStartPayload, cursor: FSMCursor) -> None:
    clear_context(cursor)
    await get_weekly_reminder(payload).subscribe_chat(
        chat_id=payload.chat_id,
        username=payload.user.username,
        full_name=payload.user.name,
    )
    await payload.send(
        "Здравствуйте! Выберите, что вас интересует, а я помогу сориентироваться и оставить заявку.",
        keyboard=main_menu_keyboard(),
    )


@router.on_command("start")
async def command_start(command: CommandContext, cursor: FSMCursor) -> None:
    clear_context(cursor)

    if command.message.recipient.chat_type == "dialog" and command.message.recipient.chat_id is not None:
        await get_weekly_reminder(command).subscribe_chat(
            chat_id=command.message.recipient.chat_id,
            username=command.sender.username,
            full_name=command.sender.name,
        )

    await command.send(
        "Здравствуйте! Выберите, что вас интересует, а я помогу сориентироваться и оставить заявку.",
        keyboard=main_menu_keyboard(),
    )


@router.on_command("stop")
async def command_stop(command: CommandContext, cursor: FSMCursor) -> None:
    clear_context(cursor)

    if command.message.recipient.chat_type == "dialog" and command.message.recipient.chat_id is not None:
        await get_weekly_reminder(command).unsubscribe_chat(command.message.recipient.chat_id)

    await command.send(
        "Хорошо, больше не буду вас беспокоить 😞 Если захотите вернуться, просто отправьте /start.",
    )


@router.on_button_callback("menu:root")
async def menu_root(callback: Callback, cursor: FSMCursor) -> None:
    message = HandlersHelper.callback_message(callback)
    if message is None:
        return

    clear_context(cursor)
    await HandlersHelper.safe_edit_text(message, "Выберите, что вас интересует:", reply_markup=main_menu_keyboard())


@router.on_button_callback("menu:about")
async def menu_about(callback: Callback) -> None:
    message = HandlersHelper.callback_message(callback)
    if message is None:
        return

    await HandlersHelper.safe_edit_text(
        message,
        "<b>О нашем клубе</b>\n\nВыберите, что хотите узнать:",
        reply_markup=about_club_keyboard(),
    )


@router.on_button_callback("about:support")
async def about_support(callback: Callback) -> None:
    message = HandlersHelper.callback_message(callback)
    if message is None:
        return

    await HandlersHelper.safe_edit_text(
        message,
        f"<b>Связь с поддержкой</b>\n\nЕсли вам удобнее связаться напрямую, позвоните по номеру: {SUPPORT_PHONE}",
        reply_markup=about_club_back_keyboard(),
    )


@router.on_button_callback("about:route")
async def about_route(callback: Callback) -> None:
    message = HandlersHelper.callback_message(callback)
    if message is None:
        return

    await HandlersHelper.safe_edit_text(
        message,
        f"<b>Как добраться</b>\n\n{ROUTE_TEXT}",
        reply_markup=route_keyboard(),
    )


@router.on_button_callback("menu:activities")
async def menu_activities(callback: Callback) -> None:
    message = HandlersHelper.callback_message(callback)
    if message is None:
        return

    await HandlersHelper.safe_edit_text(
        message,
        "Выберите активность, которая вам интересна, и я покажу основную информацию.",
        reply_markup=activities_keyboard(),
    )


@router.on_button_callback("menu:rent")
async def menu_rent(callback: Callback) -> None:
    message = HandlersHelper.callback_message(callback)
    if message is None:
        return

    await HandlersHelper.safe_edit_text(
        message,
        "Выберите, что вам нужно: проживание или площадка для отдыха.",
        reply_markup=rent_keyboard(),
    )


@router.on_button_callback("rent:stay")
async def menu_rent_stay(callback: Callback) -> None:
    message = HandlersHelper.callback_message(callback)
    if message is None:
        return

    await HandlersHelper.safe_edit_text(message, "Выберите вариант проживания:", reply_markup=rent_stay_keyboard())


@router.on_button_callback("rent:spaces")
async def menu_rent_spaces(callback: Callback, cursor: FSMCursor) -> None:
    message = HandlersHelper.callback_message(callback)
    if message is None:
        return

    data = get_state_data(cursor)
    corporate_group_label = data.get("corporate_group_label") if isinstance(data.get("corporate_group_label"), str) else None
    corporate_activities = [str(value) for value in data.get("corporate_activities", []) if isinstance(value, str)]
    requester_label = data.get("requester_label") if isinstance(data.get("requester_label"), str) else None
    requester_id = data.get("requester_id") if isinstance(data.get("requester_id"), int) else None

    clear_context(cursor)

    restore_payload: dict[str, Any] = {}

    if corporate_group_label:
        restore_payload["corporate_group_label"] = corporate_group_label

    if corporate_activities:
        restore_payload["corporate_activities"] = corporate_activities

    if requester_label:
        restore_payload["requester_label"] = requester_label

    if requester_id is not None:
        restore_payload["requester_id"] = requester_id

    if restore_payload:
        update_state_data(cursor, **restore_payload)

    await HandlersHelper.safe_edit_text(
        message,
        "Сколько человек планируется? Выберите диапазон, и я покажу подходящие площадки.",
        reply_markup=rent_spaces_group_keyboard(),
    )


@router.on_button_callback(lambda callback: (callback.payload or "").startswith("rent:spaces:size:"))
async def rent_spaces_group_selected(callback: Callback, cursor: FSMCursor) -> None:
    message = HandlersHelper.callback_message(callback)
    data = callback.payload
    if message is None or data is None:
        return

    group_key = data.split(":", 3)[3]
    group_label = RENT_SPACE_GROUP_LABELS.get(group_key)
    if group_label is None:
        await callback.answer(notification="Не удалось определить количество гостей")
        return

    update_state_data(cursor, rent_space_group_key=group_key, rent_space_group_label=group_label)
    await HandlersHelper.safe_edit_text(
        message,
        f"Подходящие площадки для группы {group_label}:",
        reply_markup=rent_spaces_keyboard(group_key),
    )


@router.on_button_callback("extras:corporate")
async def extras_corporate(callback: Callback, cursor: FSMCursor) -> None:
    message = HandlersHelper.callback_message(callback)
    if message is None:
        return

    await HandlersHelper.show_additional_services(message, cursor, "corporate")


@router.on_button_callback(lambda callback: (callback.payload or "").startswith("extras:toggle:"))
async def extras_toggle(callback: Callback, cursor: FSMCursor) -> None:
    message = HandlersHelper.callback_message(callback)
    data = callback.payload
    if message is None or data is None:
        return

    _, _, source, service_key = data.split(":", 3)
    valid_sources = set(EXTRAS_SOURCE_CONFIG) | {"rent_space_request"}
    if source not in valid_sources or service_key not in ADDITIONAL_SERVICE_LABELS:
        await callback.answer(notification="Не удалось определить услугу")
        return

    state_data = get_state_data(cursor)
    selected = [str(value) for value in state_data.get("selected_additional_services", []) if isinstance(value, str)]

    if service_key in selected:
        selected = [value for value in selected if value != service_key]
    else:
        selected.append(service_key)

    update_state_data(cursor, selected_additional_services=selected)
    await HandlersHelper.show_additional_services(message, cursor, source)


@router.on_button_callback(lambda callback: (callback.payload or "").startswith("extras:done:"))
async def extras_done(callback: Callback, cursor: FSMCursor) -> None:
    message = HandlersHelper.callback_message(callback)
    data = callback.payload
    if message is None or data is None:
        return

    source = data.split(":", 2)[2]
    if source == "rent_space_request":
        state_data = get_state_data(cursor)
        target = state_data.get("target")
        selection_path = [str(value) for value in state_data.get("selection_path", []) if isinstance(value, str)]
        requester_label = state_data.get("requester_label") if isinstance(state_data.get("requester_label"), str) else None
        requester_id = state_data.get("requester_id") if isinstance(state_data.get("requester_id"), int) else None
        selected_additional_services = [
            str(value) for value in state_data.get("selected_additional_services", []) if isinstance(value, str)
        ]

        if not isinstance(target, str) or not target:
            await callback.answer(notification="Не получилось продолжить оформление")
            return

        await HandlersHelper.start_request_flow(
            message=message,
            cursor=cursor,
            target=target,
            selection_path=selection_path,
            requester_label=requester_label,
            requester_id=requester_id,
            selected_additional_services=selected_additional_services,
            skip_additional_services_step=True,
        )
        await callback.answer(notification="Ваш выбор сохранен")
        return

    if source not in EXTRAS_SOURCE_CONFIG:
        return

    await HandlersHelper.show_corporate_activities(message, cursor)
    await callback.answer(notification="Ваш выбор сохранен")


@router.on_button_callback("menu:corporate")
async def menu_corporate(callback: Callback, cursor: FSMCursor) -> None:
    message = HandlersHelper.callback_message(callback)
    if message is None:
        return

    existing_data = get_state_data(cursor)
    selected_additional_services = [
        str(value) for value in existing_data.get("selected_additional_services", []) if isinstance(value, str)
    ]

    update_state_data(
        cursor,
        corporate_group_key=None,
        corporate_group_label=None,
        corporate_activities=[],
        selection_path=["Корпоратив"],
        selected_additional_services=selected_additional_services,
    )
    await HandlersHelper.safe_edit_text(
        message,
        f"<b>Корпоратив</b>\n\n{CORPORATE_INFO}\n\nВыберите примерный размер вашей группы:",
        reply_markup=corporate_group_keyboard(),
    )


@router.on_button_callback("corp:menu")
async def corporate_menu_file(callback: Callback) -> None:
    message = HandlersHelper.callback_message(callback)
    if message is None:
        return

    await message.send(CORPORATE_CATERING_INFO)

    if CORPORATE_MENU_FILE_PATH.is_file() and message.bot is not None:
        attachment = await message.bot.upload_file(str(CORPORATE_MENU_FILE_PATH))
        await message.send(
            "Банкетное меню в PDF-файле.",
            attachments=attachment,
        )


@router.on_button_callback(lambda callback: (callback.payload or "").startswith("corp:size:"))
async def corporate_group_selected(callback: Callback, cursor: FSMCursor) -> None:
    message = HandlersHelper.callback_message(callback)
    data = callback.payload
    if message is None or data is None:
        return

    group_key = data.split(":", 2)[2]
    group_label = CORPORATE_GROUP_LABELS.get(group_key)
    if group_label is None:
        await callback.answer(notification="Не удалось определить размер группы")
        return

    update_state_data(
        cursor,
        corporate_group_key=group_key,
        corporate_group_label=group_label,
        corporate_activities=[],
        selection_path=["Корпоратив", group_label],
    )
    await HandlersHelper.show_corporate_activities(message, cursor)


@router.on_button_callback(lambda callback: (callback.payload or "").startswith("corp:activity:"))
async def corporate_activity_toggle(callback: Callback, cursor: FSMCursor) -> None:
    message = HandlersHelper.callback_message(callback)
    data = callback.payload
    if message is None or data is None:
        return

    activity_key = data.split(":", 2)[2]
    if activity_key not in CORPORATE_ACTIVITY_LABELS:
        await callback.answer(notification="Не удалось определить активность")
        return

    raw_selected = get_state_data(cursor).get("corporate_activities", [])
    selected = [str(value) for value in raw_selected if isinstance(value, str)]

    if activity_key in selected:
        selected = [value for value in selected if value != activity_key]
    else:
        selected.append(activity_key)

    update_state_data(cursor, corporate_activities=selected)
    await HandlersHelper.show_corporate_activities(message, cursor)


@router.on_button_callback("corp:done")
async def corporate_done(callback: Callback, cursor: FSMCursor) -> None:
    message = HandlersHelper.callback_message(callback)
    if message is None:
        return

    data = get_state_data(cursor)
    group_label = data.get("corporate_group_label") if isinstance(data.get("corporate_group_label"), str) else None
    activity_keys = [str(value) for value in data.get("corporate_activities", []) if isinstance(value, str)]
    selected_services = [str(value) for value in data.get("selected_additional_services", []) if isinstance(value, str)]

    if group_label is None:
        await callback.answer(notification="Сначала выберите размер группы")
        return

    activity_labels = [CORPORATE_ACTIVITY_LABELS[key] for key in activity_keys if key in CORPORATE_ACTIVITY_LABELS]
    service_labels = [ADDITIONAL_SERVICE_LABELS[key] for key in selected_services if key in ADDITIONAL_SERVICE_LABELS]
    selection_path = ["Корпоратив", group_label]
    selection_path.extend(activity_labels or ["Активности не выбраны"])
    update_state_data(cursor, selection_path=selection_path)

    await HandlersHelper.safe_edit_text(
        message,
        "<b>Корпоратив</b>\n\n"
        f"Размер вашей группы: {group_label}\n"
        f"Что вам интересно: {', '.join(activity_labels) if activity_labels else 'пока не выбрано'}\n"
        f"Дополнительные услуги: {', '.join(service_labels) if service_labels else 'не выбраны'}\n\n"
        "Если все верно, отправьте заявку, и мы свяжемся с вами с готовым предложением.",
        reply_markup=request_button("corporate"),
    )


@router.on_button_callback("menu:event")
async def menu_event(callback: Callback, cursor: FSMCursor) -> None:
    message = HandlersHelper.callback_message(callback)
    if message is None:
        return

    update_state_data(cursor, selection_path=["Мероприятие"])
    await HandlersHelper.safe_edit_text(message, EVENT_INFO, reply_markup=request_button("event"))


@router.on_button_callback(lambda callback: (callback.payload or "").startswith("karting:info:"))
async def show_karting_info(callback: Callback, cursor: FSMCursor) -> None:
    message = HandlersHelper.callback_message(callback)
    data = callback.payload
    if message is None or data is None:
        return

    info_key = data.split(":", 2)[2]
    faq_item = KARTING_FAQ.get(info_key)
    if faq_item is None:
        await callback.answer(notification="Не удалось открыть раздел")
        return

    title, answer = faq_item
    update_state_data(cursor, selection_path=["Развлечения", "Картинг", title])
    await HandlersHelper.safe_edit_text(
        message,
        f"<b>Картинг</b>\n\n<b>{title}</b>\n{answer}",
        reply_markup=karting_info_keyboard(),
    )


@router.on_button_callback(lambda callback: (callback.payload or "").startswith("item:"))
async def show_item(callback: Callback, cursor: FSMCursor) -> None:
    message = HandlersHelper.callback_message(callback)
    data = callback.payload
    if message is None or data is None:
        return

    item_key = data.split(":", 1)[1]
    item = ITEMS_BY_KEY[item_key]
    state_data = get_state_data(cursor)
    rent_space_group_label = (
        state_data.get("rent_space_group_label")
        if isinstance(state_data.get("rent_space_group_label"), str)
        else None
    )

    if item.key == "karting":
        update_state_data(cursor, selection_path=[item.category_label, item.title])
        await HandlersHelper.safe_edit_text(
            message,
            f"<b>{item.title}</b>\n\n{item.description}\n\nВыберите, что именно хотите узнать:",
            reply_markup=karting_info_keyboard(),
        )
        return

    selection_path = [item.category_label, item.title]
    if item.category_label == "Аренда / Где посидеть" and rent_space_group_label:
        selection_path = [item.category_label, rent_space_group_label, item.title]

    update_state_data(cursor, selection_path=selection_path, selected_additional_services=[])
    await HandlersHelper.safe_edit_text(
        message,
        f"<b>{item.title}</b>\n\n{item.description}",
        reply_markup=request_button(item.key),
    )
