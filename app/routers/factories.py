from typing import List

from fastapi import APIRouter, Body, Depends, Form, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..exceptions import DuplicateError, NotFoundError

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
    name: str = Form(...),
    db: Session = Depends(get_db)
):
    """Создаёт новую фабрику."""
    factory_create = schemas.FactoryCreate(name=name)
    return crud.create_factory(db=db, factory_data=factory_create)


@router.get('/', response_model=List[schemas.Factory])
def read_factories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Получает список фабрик с пагинацией."""
    return crud.get_factories(db, skip=skip, limit=limit)


@router.get('/{factory_id}', response_model=schemas.FactoryFull)
def read_factory(
    factory_id: int,
    db: Session = Depends(get_db)
):
    """Получает фабрику по её ID."""
    factory = crud.get_factory(db, factory_id=factory_id)
    if factory is None:
        raise NotFoundError('Фабрика не найдена')
    return factory


@router.put('/{factory_id}', response_model=schemas.Factory)
def update_factory_endpoint(
    factory_id: int,
    factory_update: schemas.FactoryUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """Обновляет фабрику."""
    return crud.update_factory(
        db=db,
        factory_id=factory_id,
        factory_data=factory_update
    )


@router.delete('/{factory_id}', response_model=schemas.Factory)
def delete_factory_endpoint(
    factory_id: int,
    db: Session = Depends(get_db)
):
    """Удаляет фабрику."""
    return crud.delete_factory(db=db, factory_id=factory_id)
