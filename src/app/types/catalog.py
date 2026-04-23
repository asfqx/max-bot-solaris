from dataclasses import dataclass


@dataclass(frozen=True)
class CatalogItem:
    
    key: str
    title: str
    description: str
    category_label: str
    price: float | None = None
    quantity: float = 1.0
    max_people: int | None = None
