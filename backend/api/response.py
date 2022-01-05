from dataclasses import dataclass


@dataclass
class ShoppingListGetResponse:
    id: str
    template: str
    image: str
    cooking_time: str
