from typing import List

from fastapi import (
    APIRouter, Body, Depends, HTTPException, Query, status
)
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..exceptions import (
    NotFoundError, DuplicateError, RelatedEntityNotFoundError,
    DependentActiveChildError, AlreadyInactiveError, AlreadyActiveError
)

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
    section_data: schemas.SectionCreate = Body(...),
    db: Session = Depends(get_db)
):
    """Создаёт новый участок."""
    try:
        return crud.create_section(db=db, section_data=section_data)
    except DuplicateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except RelatedEntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.get('/', response_model=List[schemas.Section])
def read_sections(
    skip: int = 0,
    limit: int = 100,
    include_inactive: bool = Query(
        False, description='Включить неактивные участки'
    ),
    db: Session = Depends(get_db)
):
    """Получает список участков (по умолчанию только активные)."""
    return crud.get_sections(
        db, skip=skip, limit=limit, only_active=not include_inactive
    )


@router.get('/{section_id}', response_model=schemas.SectionFull)
def read_section(
    section_id: int,
    include_inactive: bool = Query(
        False, description='Получить участок даже если он неактивен'
    ),
    db: Session = Depends(get_db)
):
    """Получает участок по его ID."""
    section = crud.get_section(
        db, section_id=section_id, only_active=not include_inactive
    )
    if section is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Участок не найден или не соответствует критерию активности.'
        )
    return section


@router.put('/{section_id}', response_model=schemas.SectionFull)
def update_section_endpoint(
    section_id: int,
    section_update: schemas.SectionUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """Обновляет активный участок."""
    try:
        return crud.update_section(
            db=db, section_id=section_id, section_data=section_update
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except DuplicateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except RelatedEntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.delete(
    '/{section_id}',
    response_model=schemas.Section,
    summary='Деактивировать участок'
)
def soft_delete_section_endpoint(
    section_id: int,
    db: Session = Depends(get_db)
):
    """Мягко удаляет (деактивирует) участок."""
    try:
        return crud.soft_delete_section(db=db, section_id=section_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except DependentActiveChildError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e)
        )
    except AlreadyInactiveError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.put(
    '/{section_id}/activate',
    response_model=schemas.Section,
    summary='Активировать участок'
)
def activate_section_endpoint(
    section_id: int,
    db: Session = Depends(get_db)
):
    """Активирует ранее деактивированный участок."""
    try:
        return crud.activate_section(db=db, section_id=section_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except AlreadyActiveError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
