from aiomax.buttons import CallbackButton, ContactButton, KeyboardBuilder, LinkButton

from app.catalog import (
    ACTIVITIES,
    CLUB_MAP_URL,
    CLUB_SITE_URL,
    CORPORATE_ACTIVITIES,
    CORPORATE_GROUP_SIZES,
    KARTING_FAQ,
    RENT_SPACE_GROUP_SIZES,
    RENT_STAY,
    rent_spaces_for_group,
)
from app.max.const import ADDITIONAL_SERVICE_OPTIONS


def main_menu_keyboard() -> KeyboardBuilder:
    builder = KeyboardBuilder()
    builder.row(CallbackButton("Активности", "menu:activities"))
    builder.row(CallbackButton("Аренда", "menu:rent"))
    builder.row(CallbackButton("Корпоратив", "menu:corporate"))
    builder.row(CallbackButton("Мероприятие", "menu:event"))
    builder.row(CallbackButton("О нашем клубе", "menu:about"))
    return builder


def about_club_keyboard() -> KeyboardBuilder:
    builder = KeyboardBuilder()
    builder.row(LinkButton("Сайт", CLUB_SITE_URL))
    builder.row(CallbackButton("Связь с поддержкой", "about:support"))
    builder.row(CallbackButton("Как добраться?", "about:route"))
    builder.row(CallbackButton("В главное меню", "menu:root"))
    return builder


def about_club_back_keyboard() -> KeyboardBuilder:
    builder = KeyboardBuilder()
    builder.row(CallbackButton("Назад", "menu:about"))
    builder.row(CallbackButton("В главное меню", "menu:root"))
    return builder


def route_keyboard() -> KeyboardBuilder:
    builder = KeyboardBuilder()
    builder.row(LinkButton("Открыть карту", CLUB_MAP_URL))
    builder.row(CallbackButton("Назад", "menu:about"))
    builder.row(CallbackButton("В главное меню", "menu:root"))
    return builder


def additional_services_keyboard(source: str, back_callback: str, selected: list[str]) -> KeyboardBuilder:
    builder = KeyboardBuilder()
    selected_set = set(selected)

    for key, label in ADDITIONAL_SERVICE_OPTIONS:
        prefix = "[x] " if key in selected_set else "[ ] "
        builder.row(CallbackButton(f"{prefix}{label}", f"extras:toggle:{source}:{key}"))

    builder.row(CallbackButton("Продолжить", f"extras:done:{source}"))
    builder.row(CallbackButton("Назад", back_callback))
    builder.row(CallbackButton("В главное меню", "menu:root"))
    return builder


def activities_keyboard() -> KeyboardBuilder:
    builder = KeyboardBuilder()
    for item in ACTIVITIES:
        builder.row(CallbackButton(item.title, f"item:{item.key}"))
    builder.row(CallbackButton("Назад", "menu:root"))
    return builder


def rent_keyboard() -> KeyboardBuilder:
    builder = KeyboardBuilder()
    builder.row(CallbackButton("Где пожить", "rent:stay"))
    builder.row(CallbackButton("Где посидеть", "rent:spaces"))
    builder.row(CallbackButton("Назад", "menu:root"))
    return builder


def rent_stay_keyboard() -> KeyboardBuilder:
    builder = KeyboardBuilder()
    for item in RENT_STAY:
        builder.row(CallbackButton(item.title, f"item:{item.key}"))
    builder.row(CallbackButton("Назад", "menu:rent"))
    return builder


def rent_spaces_group_keyboard() -> KeyboardBuilder:
    builder = KeyboardBuilder()
    for key, label in RENT_SPACE_GROUP_SIZES:
        builder.row(CallbackButton(label, f"rent:spaces:size:{key}"))
    builder.row(CallbackButton("Назад", "menu:rent"))
    return builder


def rent_spaces_keyboard(group_key: str) -> KeyboardBuilder:
    builder = KeyboardBuilder()
    for item in rent_spaces_for_group(group_key):
        builder.row(CallbackButton(item.title, f"item:{item.key}"))
    builder.row(CallbackButton("К выбору количества гостей", "rent:spaces"))
    builder.row(CallbackButton("Назад", "menu:rent"))
    return builder


def corporate_group_keyboard() -> KeyboardBuilder:
    builder = KeyboardBuilder()
    for key, label in CORPORATE_GROUP_SIZES:
        builder.row(CallbackButton(label, f"corp:size:{key}"))
    builder.row(CallbackButton("Банкетное меню", "corp:menu"))
    builder.row(CallbackButton("В главное меню", "menu:root"))
    return builder


def request_people_count_keyboard() -> KeyboardBuilder:
    builder = KeyboardBuilder()
    for key, label in CORPORATE_GROUP_SIZES:
        builder.row(CallbackButton(label, f"request:size:{key}"))
    return builder


def corporate_activities_keyboard(selected: list[str]) -> KeyboardBuilder:
    builder = KeyboardBuilder()
    selected_set = set(selected)
    for key, label in CORPORATE_ACTIVITIES:
        prefix = "[x] " if key in selected_set else "[ ] "
        builder.row(CallbackButton(f"{prefix}{label}", f"corp:activity:{key}"))
    builder.row(CallbackButton("Банкетное меню", "corp:menu"))
    builder.row(CallbackButton("Дополнительные услуги", "extras:corporate"))
    builder.row(CallbackButton("Продолжить", "corp:done"))
    builder.row(CallbackButton("К размерам групп", "menu:corporate"))
    return builder


def karting_info_keyboard() -> KeyboardBuilder:
    builder = KeyboardBuilder()
    for key, (title, _) in KARTING_FAQ.items():
        builder.row(CallbackButton(title, f"karting:info:{key}"))
    builder.row(CallbackButton("Записаться", "request:karting"))
    builder.row(CallbackButton("К активностям", "menu:activities"))
    return builder


def request_button(target: str) -> KeyboardBuilder:
    builder = KeyboardBuilder()
    builder.row(CallbackButton("Оставить заявку", f"request:{target}"))
    builder.row(CallbackButton("В главное меню", "menu:root"))
    return builder


def request_confirmation_keyboard() -> KeyboardBuilder:
    builder = KeyboardBuilder()
    builder.row(CallbackButton("Отправить заявку", "request:submit"))
    builder.row(CallbackButton("Заполнить заново", "request:restart"))
    builder.row(CallbackButton("В главное меню", "menu:root"))
    return builder


def comment_skip_keyboard() -> KeyboardBuilder:
    builder = KeyboardBuilder()
    builder.row(CallbackButton("Пропустить", "request:skip_comment"))
    return builder


def phone_keyboard() -> KeyboardBuilder:
    builder = KeyboardBuilder()
    builder.row(ContactButton("Отправить номер телефона"))
    return builder
