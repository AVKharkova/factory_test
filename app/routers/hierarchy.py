from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from .. import crud, schemas, models
from ..database import get_db
from typing import Literal

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

    if entity_type == 'factory':
        factory = crud.get_factory(db, entity_id)
        if not factory:
            raise HTTPException(status_code=404, detail='Фабрика не найдена')
        entity_name = factory.name
        # У фабрики нет родителей в этой модели
        children = crud.get_children_for_factory(db, entity_id)

    elif entity_type == 'section':
        section = crud.get_section(db, entity_id)
        if not section:
            raise HTTPException(status_code=404, detail='Участок не найден')
        entity_name = section.name
        parents = crud.get_parents_for_section(db, entity_id)
        children = crud.get_children_for_section(db, entity_id)

    elif entity_type == 'equipment':
        equipment = crud.get_equipment(db, entity_id)
        if not equipment:
            raise HTTPException(status_code=404, detail='Оборудование не найдено')
        entity_name = equipment.name
        parents = crud.get_parents_for_equipment(db, entity_id)
        # У оборудования нет детей в этой модели

    else:
        raise HTTPException(status_code=400, detail='Неверный тип сущности')

    return schemas.HierarchyResponse(
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        parents=parents,
        children=children
    )
