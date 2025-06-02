from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import crud, models, schemas
from ..database import get_db

router = APIRouter(
    prefix='/equipment',
    tags=['equipment'],
)

@router.post('/', response_model=schemas.Equipment)
def create_equipment_endpoint(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    section_ids_str: Optional[str] = Form(None, alias='section_ids', description='Список ID участков через запятую'),
    db: Session = Depends(get_db)
):
    """Создаёт новое оборудование."""
    db_equipment = crud.get_equipment_by_name(db, name=name)
    if db_equipment:
        raise HTTPException(status_code=400, detail='Оборудование с таким наименованием уже существует')

    section_ids_list = []
    if section_ids_str:
        try:
            section_ids_list = [int(sid.strip()) for sid in section_ids_str.split(',') if sid.strip()]
        except ValueError:
            raise HTTPException(status_code=400, detail='Неверный формат section_ids. Должны быть целые числа через запятую.')

    equipment_create = schemas.EquipmentCreate(name=name, description=description, section_ids=section_ids_list)
    return crud.create_equipment(db=db, equipment=equipment_create)


@router.get('/', response_model=List[schemas.Equipment])
def read_equipment_list(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получает список оборудования с пагинацией."""
    equipment = crud.get_equipment_list(db, skip=skip, limit=limit)
    return equipment


@router.get('/{equipment_id}', response_model=schemas.EquipmentFull)
def read_equipment_item(equipment_id: int, db: Session = Depends(get_db)):
    """Получает оборудование по его ID."""
    db_equipment = crud.get_equipment(db, equipment_id=equipment_id)
    if db_equipment is None:
        raise HTTPException(status_code=404, detail='Оборудование не найдено')
    return db_equipment
