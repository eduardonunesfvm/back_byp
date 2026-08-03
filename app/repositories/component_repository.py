from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.component import Component
from app.schemas.component import ComponentCreate, ComponentUpdate


class ComponentRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self, category: str | None = None) -> list[Component]:
        stmt = select(Component)
        if category:
            stmt = stmt.where(Component.category == category)
        return list(self.db.scalars(stmt))

    def get_by_id(self, component_id: int) -> Component | None:
        return self.db.get(Component, component_id)

    def create(self, data: ComponentCreate) -> Component:
        comp = Component(**data.model_dump())
        self.db.add(comp)
        self.db.commit()
        self.db.refresh(comp)
        return comp

    def update(self, comp: Component, data: ComponentUpdate) -> Component:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(comp, field, value)
        self.db.commit()
        self.db.refresh(comp)
        return comp

    def delete(self, comp: Component) -> None:
        self.db.delete(comp)
        self.db.commit()
