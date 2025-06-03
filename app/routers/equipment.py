from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..exceptions import NotFoundError, DuplicateError, RelatedEntityNotFoundError, AlreadyInactiveError, AlreadyActiveError  

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
    equipment_data: schemas.EquipmentCreate = Body(...),
    db: Session = Depends(get_db)
):
    """Создаёт новое оборудование."""
    try:
        return crud.create_equipment(db=db, equipment_data=equipment_data)
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RelatedEntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get('/', response_model=List[schemas.Equipment])
def read_equipment_list(
    skip: int = 0,
    limit: int = 100,
    include_inactive: bool = Query(False, description='Включить неактивное оборудование'),
    db: Session = Depends(get_db)
):
    """Получает список оборудования (по умолчанию только активные)."""
    return crud.get_equipment_list(db, skip=skip, limit=limit, only_active=not include_inactive)

@router.get('/{equipment_id}', response_model=schemas.EquipmentFull)
def read_equipment_item(
    equipment_id: int,
    include_inactive: bool = Query(False, description='Получить оборудование даже если оно неактивно'),
    db: Session = Depends(get_db)
):
    """Получает оборудование по его ID."""
    equipment = crud.get_equipment(db, equipment_id=equipment_id, only_active=not include_inactive)
    if equipment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Оборудование не найдено или не соответствует критерию активности.')
    return equipment

@router.put('/{equipment_id}', response_model=schemas.EquipmentFull)
def update_equipment_endpoint(
    equipment_id: int,
    equipment_update: schemas.EquipmentUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """Обновляет активное оборудование."""
    try:
        return crud.update_equipment(db=db, equipment_id=equipment_id, equipment_data=equipment_update)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RelatedEntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete('/{equipment_id}', response_model=schemas.Equipment, summary='Деактивировать оборудование')
def soft_delete_equipment_endpoint(equipment_id: int, db: Session = Depends(get_db)):
    """Мягко удаляет (деактивирует) оборудование."""
    try:
        return crud.soft_delete_equipment(db=db, equipment_id=equipment_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AlreadyInactiveError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put('/{equipment_id}/activate', response_model=schemas.Equipment, summary='Активировать оборудование')
def activate_equipment_endpoint(equipment_id: int, db: Session = Depends(get_db)):
    """Активирует ранее деактивированное оборудование."""
    try:
        return crud.activate_equipment(db=db, equipment_id=equipment_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AlreadyActiveError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
