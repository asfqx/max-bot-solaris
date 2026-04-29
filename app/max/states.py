from typing import Any

from aiomax.fsm import FSMCursor


class RequestLeadState:
    waiting_for_name = "request_lead.waiting_for_name"
    waiting_for_people_count = "request_lead.waiting_for_people_count"
    waiting_for_age = "request_lead.waiting_for_age"
    waiting_for_comment = "request_lead.waiting_for_comment"
    waiting_for_booking_datetime = "request_lead.waiting_for_booking_datetime"
    waiting_for_phone = "request_lead.waiting_for_phone"
    waiting_for_event_details = "request_lead.waiting_for_event_details"
    waiting_for_confirmation = "request_lead.waiting_for_confirmation"


def get_state(cursor: FSMCursor | None) -> Any:
    if cursor is None:
        return None
    return cursor.get_state()


def set_state(cursor: FSMCursor, state: str) -> None:
    cursor.change_state(state)


def clear_context(cursor: FSMCursor | None) -> None:
    if cursor is None:
        return
    cursor.clear()


def get_state_data(cursor: FSMCursor | None) -> dict[str, Any]:
    if cursor is None:
        return {}

    data = cursor.get_data()
    if isinstance(data, dict):
        return data.copy()
    return {}


def replace_state_data(cursor: FSMCursor, data: dict[str, Any]) -> dict[str, Any]:
    cursor.change_data(data.copy())
    return data


def update_state_data(cursor: FSMCursor, **kwargs: Any) -> dict[str, Any]:
    data = get_state_data(cursor)
    data.update(kwargs)
    cursor.change_data(data)
    return data
