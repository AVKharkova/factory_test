from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from typing import List
from .. import crud, models, schemas
from ..database import get_db

router = APIRouter(
    prefix='/factories',
    tags=['factories'],
)

@router.post('/', response_model=schemas.Factory)
def create_factory_endpoint(name: str = Form(...), db: Session = Depends(get_db)):
    """Создаёт новую фабрику."""
    db_factory = crud.get_factory_by_name(db, name=name)
    if db_factory:
        raise HTTPException(status_code=400, detail='Фабрика с таким наименованием уже зарегистрирована')
    factory_create = schemas.FactoryCreate(name=name)
    return crud.create_factory(db=db, factory=factory_create)


@router.get('/', response_model=List[schemas.Factory])
def read_factories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получает список фабрик с пагинацией."""
    factories = crud.get_factories(db, skip=skip, limit=limit)
    return factories


@router.get('/{factory_id}', response_model=schemas.FactoryFull)
def read_factory(factory_id: int, db: Session = Depends(get_db)):
    """Получает фабрику по её ID."""
    db_factory = crud.get_factory(db, factory_id=factory_id)
    if db_factory is None:
        raise HTTPException(status_code=404, detail='Фабрика не найдена')
    return db_factory
