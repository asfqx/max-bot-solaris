from dataclasses import dataclass


@dataclass(frozen=True)
class RequestContext:
    
    item_title: str
    category: str
    event_details: str | None = None


@dataclass(frozen=True)
class RequestLeadSubmission:
    
    target: str
    name: str
    phone: str
    title: str
    item_title: str
    category: str
    selection_path: tuple[str, ...]
    comments: str
    people_count: str | None = None
    age: str | None = None
    comment: str | None = None
    booking_datetime: str | None = None
    selected_additional_services: tuple[str, ...] = ()
    event_details: str | None = None
