from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..exceptions import NotFoundError, DuplicateError, DependentActiveChildError, AlreadyInactiveError, AlreadyActiveError  

router = APIRouter(
    prefix='/factories',
    tags=['factories'],
)

@router.post(
    '/',
    response_model=schemas.Factory,
    status_code=status.HTTP_201_CREATED
)
def create_factory_endpoint(
    factory_data: schemas.FactoryCreate = Body(...),
    db: Session = Depends(get_db)
):
    """Создаёт новую фабрику."""
    try:
        return crud.create_factory(db=db, factory_data=factory_data)
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get('/', response_model=List[schemas.Factory])
def read_factories(
    skip: int = 0,
    limit: int = 100,
    include_inactive: bool = Query(False, description='Включить неактивные фабрики'),
    db: Session = Depends(get_db)
):
    """Получает список фабрик (по умолчанию только активные)."""
    return crud.get_factories(db, skip=skip, limit=limit, only_active=not include_inactive)

@router.get('/{factory_id}', response_model=schemas.FactoryFull)
def read_factory(
    factory_id: int,
    include_inactive: bool = Query(False, description='Получить фабрику даже если она неактивна'),
    db: Session = Depends(get_db)
):
    """Получает фабрику по её ID."""
    factory = crud.get_factory(db, factory_id=factory_id, only_active=not include_inactive)
    if factory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Фабрика не найдена или не соответствует критерию активности.')
    return factory

@router.put('/{factory_id}', response_model=schemas.Factory)
def update_factory_endpoint(
    factory_id: int,
    factory_update: schemas.FactoryUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """Обновляет активную фабрику."""
    try:
        return crud.update_factory(db=db, factory_id=factory_id, factory_data=factory_update)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete('/{factory_id}', response_model=schemas.Factory, summary='Деактивировать фабрику')
def soft_delete_factory_endpoint(factory_id: int, db: Session = Depends(get_db)):
    """Мягко удаляет (деактивирует) фабрику."""
    try:
        return crud.soft_delete_factory(db=db, factory_id=factory_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DependentActiveChildError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except AlreadyInactiveError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put('/{factory_id}/activate', response_model=schemas.Factory, summary='Активировать фабрику')
def activate_factory_endpoint(factory_id: int, db: Session = Depends(get_db)):
    """Активирует ранее деактивированную фабрику."""
    try:
        return crud.activate_factory(db=db, factory_id=factory_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AlreadyActiveError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
