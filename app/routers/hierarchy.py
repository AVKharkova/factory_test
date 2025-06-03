from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..exceptions import NotFoundError

router = APIRouter(
    prefix='/hierarchy',
    tags=['hierarchy'],
)


@router.get('/', response_model=schemas.HierarchyResponse)
def get_entity_hierarchy(
    entity_type: Literal['factory', 'section', 'equipment'] = Query(..., description='Тип сущности'),
    entity_id: int = Query(..., description='ID сущности'),
    db: Session = Depends(get_db)
):
    """Получает иерархию для указанной сущности."""
    parents = []
    children = []
    entity_name = ''
    entity = None

    if entity_type == 'factory':
        entity = crud.get_factory(db, entity_id)
        if entity:
            entity_name = entity.name
            children = crud.get_children_for_factory(db, entity_id)

    elif entity_type == 'section':
        entity = crud.get_section(db, entity_id)
        if entity:
            entity_name = entity.name
            parents = crud.get_parents_for_section(db, entity_id)
            children = crud.get_children_for_section(db, entity_id)

    elif entity_type == 'equipment':
        entity = crud.get_equipment(db, entity_id)
        if entity:
            entity_name = entity.name
            parents = crud.get_parents_for_equipment(db, entity_id)

    if not entity:
        raise NotFoundError(f'{entity_type.capitalize()} с ID {entity_id} не найден(а)')

    return schemas.HierarchyResponse(
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        parents=parents,
        children=children
    )
