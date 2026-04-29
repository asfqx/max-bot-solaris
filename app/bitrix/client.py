import re
from types import TracebackType
from typing import Any

import httpx

from .exceptions import BitrixAPIError


class BitrixClient:
    
    def __init__(
        self,
        webhook_url: str,
        source_id: str = "WEB",
        assigned_by_id: int | None = None,
        lead_status_id: str = "NEW",
    ) -> None:
        
        self._webhook_url = webhook_url.rstrip("/")
        self._source_id = source_id
        self._assigned_by_id = assigned_by_id
        self._lead_status_id = lead_status_id.strip() or "NEW"
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "BitrixClient":
        
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=20.0)
            
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def call(self, method: str, payload: dict[str, Any] | None = None) -> Any:
        
        if self._client is None:
            raise RuntimeError("BitrixClient is not connected. Use 'async with BitrixClient(...)'.")

        form_payload = self._flatten_payload(payload or {})
        try:
            response = await self._client.post(
                f"{self._webhook_url}/{method}.json",
                data=form_payload,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            response = exc.response
            response_preview = response.text.strip().replace("\n", " ")[:300]
            details = f"Bitrix HTTP {response.status_code} for {method}"
            if response_preview:
                details = f"{details}: {response_preview}"
            raise BitrixAPIError(details) from exc
        except httpx.HTTPError as exc:
            raise BitrixAPIError(f"Bitrix request failed for {method}: {exc}") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise BitrixAPIError(f"Bitrix returned non-JSON response: {response.text[:200]}") from exc

        if "error" in data:
            raise BitrixAPIError(f"{data['error']}: {data.get('error_description', '')}".strip())

        return data.get("result")

    async def find_lead_by_phone(self, phone: str) -> int | None:
        
        variants = self._phone_variants(phone)

        try:
            result = await self.call(
                "crm.duplicate.findbycomm",
                {"type": "PHONE", "values": variants, "entity_type": "LEAD"},
            )
        except BitrixAPIError:
            result = None

        if isinstance(result, dict):
            lead_ids: list[str] = result.get("LEAD") or result.get("lead", [])
            if lead_ids:
                return int(lead_ids[0])

        for variant in variants:
            result = await self.call(
                "crm.lead.list",
                {
                    "filter": {"PHONE": variant},
                    "select": ["ID"],
                    "order": {"ID": "ASC"},
                },
            )
            if result:
                return int(result[0]["ID"])

        return None

    async def get_lead(self, lead_id: int) -> dict[str, Any]:
        
        return await self.call("crm.lead.get", {"id": lead_id})

    async def create_lead(self, *, name: str, phone: str, title: str, comments: str) -> int:
        
        fields: dict[str, Any] = {
            "TITLE": title,
            "NAME": name,
            "COMMENTS": comments,
            "PHONE": [{"VALUE": phone, "VALUE_TYPE": "WORK"}],
            "SOURCE_ID": self._source_id,
            "STATUS_ID": self._lead_status_id,
        }

        if self._assigned_by_id is not None:
            fields["ASSIGNED_BY_ID"] = self._assigned_by_id

        result = await self.call("crm.lead.add", {"fields": fields})
        
        return int(result)

    async def update_lead_context(self, lead_id: int, *, title: str, name: str, comments: str) -> None:
        
        lead = await self.get_lead(lead_id)
        updates: dict[str, Any] = {}

        current_status = (lead.get("STATUS_ID") or "").strip()
        if current_status != self._lead_status_id:
            updates["STATUS_ID"] = self._lead_status_id

        next_title = title.strip()
        current_title = (lead.get("TITLE") or "").strip()
        if next_title and current_title != next_title:
            updates["TITLE"] = next_title

        current_name = (lead.get("NAME") or "").strip()
        if not current_name and name.strip():
            updates["NAME"] = name.strip()

        current_comments = (lead.get("COMMENTS") or "").strip()
        if comments.strip() and comments.strip() not in current_comments:
            updates["COMMENTS"] = f"{current_comments}\n\n{comments}".strip() if current_comments else comments.strip()

        if updates:
            await self.call("crm.lead.update", {"id": lead_id, "fields": updates})

    @staticmethod
    def build_comments(
        *,
        category: str,
        item_title: str,
        max_user: str,
        max_id: int,
        event_details: str | None = None,
        selected_options: list[str] | None = None,
        people_count: str | None = None,
        age: str | None = None,
        comment: str | None = None,
        booking_datetime: str | None = None,
        selected_additional_services: list[str] | None = None,
    ) -> str:
        lines = [
            "Источник: Max-бот",
            f"Категория: {category}",
            f"Интерес клиента: {item_title}",
            f"Пользователь Max: {max_user}",
            f"Max ID: {max_id}",
        ]

        if selected_options:
            lines.append(f"Что выбрал пользователь: {' -> '.join(selected_options)}")

        if people_count:
            lines.append(f"Количество человек: {people_count}")

        if age:
            lines.append(f"Возраст участников: {age}")

        if booking_datetime:
            lines.append(f"Дата и время брони: {booking_datetime}")

        if selected_additional_services:
            lines.append("Дополнительные услуги: " + ", ".join(selected_additional_services))

        if event_details:
            lines.append(f"Описание запроса: {event_details}")

        if comment:
            lines.append(f"Комментарий клиента: {comment}")

        return "\n".join(lines)

    @staticmethod
    def _flatten_payload(payload: dict[str, Any]) -> dict[str, str]:
        
        items: dict[str, str] = {}

        def walk(prefix: str, value: Any) -> None:
            if value is None:
                return
            if isinstance(value, dict):
                for key, nested_value in value.items():
                    next_prefix = f"{prefix}[{key}]" if prefix else str(key)
                    walk(next_prefix, nested_value)
                return
            if isinstance(value, (list, tuple)):
                for index, nested_value in enumerate(value):
                    walk(f"{prefix}[{index}]", nested_value)
                return
            items[prefix] = str(value)

        for key, value in payload.items():
            walk(str(key), value)

        return items

    @staticmethod
    def _phone_variants(phone: str) -> list[str]:
        
        raw = phone.strip()
        digits = re.sub(r"\D", "", raw)
        variants = [raw]

        if digits:
            variants.append(digits)
            
            if digits.startswith("8") and len(digits) == 11:
                variants.append("7" + digits[1:])
                variants.append("+" + "7" + digits[1:])
                
            elif digits.startswith("7") and len(digits) == 11:
                variants.append("8" + digits[1:])
                variants.append("+" + digits)
                
            elif len(digits) == 10:
                variants.append("7" + digits)
                variants.append("+7" + digits)

        return list(dict.fromkeys(variants))





