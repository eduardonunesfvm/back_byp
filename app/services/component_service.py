from sqlalchemy.orm import Session

from app.core.exceptions import NotFound
from app.models.component import Component
from app.repositories.component_repository import ComponentRepository
from app.schemas.component import ComponentCreate, ComponentUpdate


class ComponentService:
    def __init__(self, db: Session, repo: ComponentRepository | None = None):
        self.db = db
        self.repo = repo or ComponentRepository(db)

    def list(self, category: str | None = None) -> list[Component]:
        return self.repo.list(category)

    def get(self, component_id: int) -> Component:
        comp = self.repo.get_by_id(component_id)
        if comp is None:
            raise NotFound()
        return comp

    def create(self, data: ComponentCreate) -> Component:
        return self.repo.create(data)

    def update(self, component_id: int, data: ComponentUpdate) -> Component:
        comp = self.get(component_id)
        return self.repo.update(comp, data)

    def delete(self, component_id: int) -> None:
        comp = self.get(component_id)
        self.repo.delete(comp)
