from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ComponentCategoryLiteral = Literal[
    "cpu", "gpu", "ram", "storage", "motherboard", "psu", "case", "cooling"
]


class ComponentBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: ComponentCategoryLiteral
    brand: str | None = Field(default=None, max_length=100)
    price: float | None = Field(default=None, ge=0)
    specs: dict | None = None


class ComponentCreate(ComponentBase):
    pass


class ComponentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    category: ComponentCategoryLiteral | None = None
    brand: str | None = Field(default=None, max_length=100)
    price: float | None = Field(default=None, ge=0)
    specs: dict | None = None


class ComponentRead(ComponentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
