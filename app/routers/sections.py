from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import crud, models, schemas
from ..database import get_db

router = APIRouter(
    prefix='/sections',
    tags=['sections'],
)

@router.post('/', response_model=schemas.Section)
def create_section_endpoint(
    name: str = Form(...),
    factory_id: int = Form(...),
    equipment_ids_str: Optional[str] = Form(None, alias='equipment_ids', description='Список ID оборудования через запятую'),
    db: Session = Depends(get_db)
):
    """Создаёт новый участок."""
    # Проверка на уникальность участка (в данной фабрике)
    db_section = db.query(models.Section).filter(models.Section.name == name, models.Section.factory_id == factory_id).first()
    if db_section:
        raise HTTPException(status_code=400, detail='Участок с таким наименованием уже существует в этой фабрике')

    equipment_ids_list = []
    if equipment_ids_str:
        try:
            equipment_ids_list = [int(eid.strip()) for eid in equipment_ids_str.split(',') if eid.strip()]
        except ValueError:
            raise HTTPException(status_code=400, detail='Неверный формат equipment_ids. Должны быть целые числа через запятую.')

    section_create = schemas.SectionCreate(name=name, factory_id=factory_id, equipment_ids=equipment_ids_list)
    created_section = crud.create_section(db=db, section=section_create)
    if created_section is None:
        raise HTTPException(status_code=404, detail=f'Фабрика с id {factory_id} не найдена')
    return created_section


@router.get('/', response_model=List[schemas.Section])
def read_sections(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получает список участков с пагинацией."""
    sections = crud.get_sections(db, skip=skip, limit=limit)
    return sections


@router.get('/{section_id}', response_model=schemas.SectionFull)
def read_section(section_id: int, db: Session = Depends(get_db)):
    """Получает участок по его ID."""
    db_section = crud.get_section(db, section_id=section_id)
    if db_section is None:
        raise HTTPException(status_code=404, detail='Участок не найден')
    return db_section
