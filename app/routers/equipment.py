from typing import List, Optional

from fastapi import APIRouter, Body, Depends, Form, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..exceptions import NotFoundError, DuplicateError, RelatedEntityNotFoundError

router = APIRouter(
    prefix='/equipment',
    tags=['equipment'],
)


@router.post(
    '/',
    response_model=schemas.Equipment,
    status_code=status.HTTP_201_CREATED
)
def create_equipment_endpoint(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    section_ids_str: Optional[str] = Form(
        None,
        alias='section_ids',
        description='Список ID участков через запятую'
    ),
    db: Session = Depends(get_db)
):
    """Создаёт новое оборудование."""
    section_ids_list = []
    if section_ids_str:
        try:
            section_ids_list = [
                int(sid.strip()) for sid in section_ids_str.split(',')
                if sid.strip()
            ]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Неверный формат section_ids. Должны быть целые числа через запятую.'
            )

    equipment_create = schemas.EquipmentCreate(
        name=name,
        description=description,
        section_ids=section_ids_list
    )
    return crud.create_equipment(db=db, equipment_data=equipment_create)


@router.get('/', response_model=List[schemas.Equipment])
def read_equipment_list(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Получает список оборудования с пагинацией."""
    return crud.get_equipment_list(db, skip=skip, limit=limit)


@router.get('/{equipment_id}', response_model=schemas.EquipmentFull)
def read_equipment_item(
    equipment_id: int,
    db: Session = Depends(get_db)
):
    """Получает оборудование по его ID."""
    equipment = crud.get_equipment(db, equipment_id=equipment_id)
    if equipment is None:
        raise NotFoundError('Оборудование не найдено')
    return equipment


@router.put('/{equipment_id}', response_model=schemas.EquipmentFull)
def update_equipment_endpoint(
    equipment_id: int,
    equipment_update: schemas.EquipmentUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """Обновляет оборудование."""
    return crud.update_equipment(
        db=db,
        equipment_id=equipment_id,
        equipment_data=equipment_update
    )


@router.delete('/{equipment_id}', response_model=schemas.Equipment)
def delete_equipment_endpoint(
    equipment_id: int,
    db: Session = Depends(get_db)
):
    """Удаляет оборудование."""
    return crud.delete_equipment(db=db, equipment_id=equipment_id)
