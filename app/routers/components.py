from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.routers.deps import get_current_admin
from app.schemas.component import ComponentCreate, ComponentRead, ComponentUpdate
from app.services.component_service import ComponentService

router = APIRouter()


def _service(db: Session) -> ComponentService:
    return ComponentService(db)


@router.get("/components", response_model=list[ComponentRead])
def list_components(
    category: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return _service(db).list(category)


@router.get("/components/{component_id}", response_model=ComponentRead)
def get_component(component_id: int, db: Session = Depends(get_db)):
    return _service(db).get(component_id)


@router.post("/components", response_model=ComponentRead, status_code=201)
def create_component(
    data: ComponentCreate,
    db: Session = Depends(get_db),
    _admin: object = Depends(get_current_admin),
):
    return _service(db).create(data)


@router.put("/components/{component_id}", response_model=ComponentRead)
def update_component(
    component_id: int,
    data: ComponentUpdate,
    db: Session = Depends(get_db),
    _admin: object = Depends(get_current_admin),
):
    return _service(db).update(component_id, data)


@router.delete("/components/{component_id}", status_code=204)
def delete_component(
    component_id: int,
    db: Session = Depends(get_db),
    _admin: object = Depends(get_current_admin),
):
    _service(db).delete(component_id)
    return None