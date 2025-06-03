from typing import List, Optional

from fastapi import APIRouter, Body, Depends, Form, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..exceptions import NotFoundError, DuplicateError, RelatedEntityNotFoundError

router = APIRouter(
    prefix='/sections',
    tags=['sections'],
)


@router.post(
    '/',
    response_model=schemas.Section,
    status_code=status.HTTP_201_CREATED
)
def create_section_endpoint(
    name: str = Form(...),
    factory_id: int = Form(...),
    equipment_ids_str: Optional[str] = Form(
        None,
        alias='equipment_ids',
        description='Список ID оборудования через запятую'
    ),
    db: Session = Depends(get_db)
):
    """Создаёт новый участок."""
    equipment_ids_list = []
    if equipment_ids_str:
        try:
            equipment_ids_list = [
                int(eid.strip()) for eid in equipment_ids_str.split(',')
                if eid.strip()
            ]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Неверный формат equipment_ids. Должны быть целые числа через запятую.'
            )

    section_create = schemas.SectionCreate(
        name=name,
        factory_id=factory_id,
        equipment_ids=equipment_ids_list
    )
    return crud.create_section(db=db, section_data=section_create)


@router.get('/', response_model=List[schemas.Section])
def read_sections(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Получает список участков с пагинацией."""
    return crud.get_sections(db, skip=skip, limit=limit)


@router.get('/{section_id}', response_model=schemas.SectionFull)
def read_section(
    section_id: int,
    db: Session = Depends(get_db)
):
    """Получает участок по его ID."""
    section = crud.get_section(db, section_id=section_id)
    if section is None:
        raise NotFoundError('Участок не найден')
    return section


@router.put('/{section_id}', response_model=schemas.SectionFull)
def update_section_endpoint(
    section_id: int,
    section_update: schemas.SectionUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """Обновляет участок."""
    return crud.update_section(
        db=db,
        section_id=section_id,
        section_data=section_update
    )


@router.delete('/{section_id}', response_model=schemas.Section)
def delete_section_endpoint(
    section_id: int,
    db: Session = Depends(get_db)
):
    """Удаляет участок."""
    return crud.delete_section(db=db, section_id=section_id)
