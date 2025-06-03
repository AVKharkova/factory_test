from typing import List, Optional, Type
from sqlalchemy.orm import Session, selectinload

from . import models, schemas
from .exceptions import (
    NotFoundError,
    RelatedEntityNotFoundError,
    DuplicateError,
    DependentActiveChildError,
    AlreadyActiveError
)


def _get_active_entity(db: Session, model: Type[models.Base], entity_id: int) -> Optional[models.Base]:
    """Получает активную сущность по её ID."""
    return db.query(model).filter(model.id == entity_id, model.is_active == True).first()


# --- CRUD для фабрик ---

def get_factory(db: Session, factory_id: int, only_active: bool = True) -> Optional[models.Factory]:
    """Получает фабрику по её ID."""
    query = db.query(models.Factory).filter(models.Factory.id == factory_id)
    if only_active:
        query = query.filter(models.Factory.is_active == True)
    return query.first()

def get_factory_by_name(db: Session, name: str, only_active: bool = True) -> Optional[models.Factory]:
    """Получает фабрику по её наименованию."""
    query = db.query(models.Factory).filter(models.Factory.name == name)
    if only_active:
        query = query.filter(models.Factory.is_active == True)
    return query.first()

def get_factories(db: Session, skip: int = 0, limit: int = 100, only_active: bool = True) -> List[models.Factory]:
    """Получает список фабрик с пагинацией."""
    query = db.query(models.Factory)
    if only_active:
        query = query.filter(models.Factory.is_active == True)
    return query.order_by(models.Factory.id).offset(skip).limit(limit).all()

def create_factory(db: Session, factory_data: schemas.FactoryCreate) -> models.Factory:
    """Создаёт новую фабрику."""
    existing_factory_any_status = db.query(models.Factory).filter(models.Factory.name == factory_data.name).first()
    if existing_factory_any_status:
        raise DuplicateError(f'Фабрика с наименованием "{factory_data.name}" уже существует (возможно, деактивирована).')
    db_factory = models.Factory(name=factory_data.name, is_active=True)
    db.add(db_factory)
    db.commit()
    db.refresh(db_factory)
    return db_factory

def update_factory(db: Session, factory_id: int, factory_data: schemas.FactoryUpdate) -> models.Factory:
    """Обновляет данные активной фабрики."""
    db_factory = _get_active_entity(db, models.Factory, factory_id)
    if not db_factory:
        raise NotFoundError(f'Активная фабрика с ID {factory_id} не найдена.')
    if factory_data.name is not None and factory_data.name != db_factory.name:
        existing_factory_any_status = db.query(models.Factory).filter(
            models.Factory.name == factory_data.name,
            models.Factory.id != factory_id
        ).first()
        if existing_factory_any_status:
            raise DuplicateError(f'Фабрика с наименованием "{factory_data.name}" уже существует (возможно, деактивирована).')
        db_factory.name = factory_data.name
    db.commit()
    db.refresh(db_factory)
    return db_factory

def soft_delete_factory(db: Session, factory_id: int) -> models.Factory:
    """Мягко удаляет (деактивирует) фабрику."""
    db_factory = _get_active_entity(db, models.Factory, factory_id)
    if not db_factory:
        raise NotFoundError(f'Активная фабрика с ID {factory_id} не найдена.')
    active_sections_count = db.query(models.Section).filter(
        models.Section.factory_id == factory_id,
        models.Section.is_active == True
    ).count()
    if active_sections_count > 0:
        raise DependentActiveChildError(
            f'Нельзя деактивировать фабрику ID {factory_id}, есть {active_sections_count} активных участков.'
        )
    db_factory.is_active = False
    db.commit()
    db.refresh(db_factory)
    return db_factory


# --- CRUD для оборудования ---

def get_equipment(db: Session, equipment_id: int, only_active: bool = True) -> Optional[models.Equipment]:
    """Получает оборудование по его ID с загрузкой связанных участков."""
    query = db.query(models.Equipment).options(
        selectinload(models.Equipment.sections)
    ).filter(models.Equipment.id == equipment_id)
    if only_active:
        query = query.filter(models.Equipment.is_active == True)
    return query.first()

def get_equipment_by_name(db: Session, name: str, only_active: bool = True) -> Optional[models.Equipment]:
    """Получает оборудование по его наименованию."""
    query = db.query(models.Equipment).filter(models.Equipment.name == name)
    if only_active:
        query = query.filter(models.Equipment.is_active == True)
    return query.first()

def get_equipment_list(db: Session, skip: int = 0, limit: int = 100, only_active: bool = True) -> List[models.Equipment]:
    """Получает список оборудования с пагинацией."""
    query = db.query(models.Equipment)
    if only_active:
        query = query.filter(models.Equipment.is_active == True)
    return query.order_by(models.Equipment.id).offset(skip).limit(limit).all()

def create_equipment(db: Session, equipment_data: schemas.EquipmentCreate) -> models.Equipment:
    """Создаёт новое оборудование с привязкой к участкам."""
    existing_equipment_any_status = db.query(models.Equipment).filter(models.Equipment.name == equipment_data.name).first()
    if existing_equipment_any_status:
        raise DuplicateError(f'Оборудование с наименованием "{equipment_data.name}" уже существует (возможно, деактивировано).')
    db_equipment = models.Equipment(
        name=equipment_data.name,
        description=equipment_data.description,
        is_active=True
    )
    found_sections = []
    missing_or_inactive_section_ids = []
    if equipment_data.section_ids:
        for section_id in equipment_data.section_ids:
            section = _get_active_entity(db, models.Section, section_id)
            if section:
                found_sections.append(section)
            else:
                missing_or_inactive_section_ids.append(section_id)
        if missing_or_inactive_section_ids:
            raise RelatedEntityNotFoundError(f'Активные участки с ID {missing_or_inactive_section_ids} не найдены.')
        db_equipment.sections.extend(found_sections)
    db.add(db_equipment)
    db.commit()
    db.refresh(db_equipment)
    return db_equipment

def update_equipment(db: Session, equipment_id: int, equipment_data: schemas.EquipmentUpdate) -> models.Equipment:
    """Обновляет данные активного оборудования."""
    db_equipment = _get_active_entity(db, models.Equipment, equipment_id)
    if not db_equipment:
        raise NotFoundError(f'Активное оборудование с ID {equipment_id} не найдено.')
    if equipment_data.name is not None and equipment_data.name != db_equipment.name:
        existing_equipment_any_status = db.query(models.Equipment).filter(
            models.Equipment.name == equipment_data.name,
            models.Equipment.id != equipment_id
        ).first()
        if existing_equipment_any_status:
            raise DuplicateError(f'Оборудование с наименованием "{equipment_data.name}" уже существует (возможно, деактивировано).')
        db_equipment.name = equipment_data.name
    if equipment_data.description is not None:
        db_equipment.description = equipment_data.description
    if equipment_data.section_ids is not None:
        new_sections = []
        missing_or_inactive_section_ids = []
        if equipment_data.section_ids:
            for section_id in equipment_data.section_ids:
                section = _get_active_entity(db, models.Section, section_id)
                if section:
                    new_sections.append(section)
                else:
                    missing_or_inactive_section_ids.append(section_id)
            if missing_or_inactive_section_ids:
                raise RelatedEntityNotFoundError(f'Активные участки с ID {missing_or_inactive_section_ids} не найдены при обновлении оборудования.')
        db_equipment.sections = new_sections
    db.commit()
    db.refresh(db_equipment)
    return db_equipment

def soft_delete_equipment(db: Session, equipment_id: int) -> models.Equipment:
    """Мягко удаляет (деактивирует) оборудование."""
    db_equipment = _get_active_entity(db, models.Equipment, equipment_id)
    if not db_equipment:
        raise NotFoundError(f'Активное оборудование с ID {equipment_id} не найдено.')
    db_equipment.is_active = False
    db.commit()
    db.refresh(db_equipment)
    return db_equipment


# --- CRUD для участков ---

def get_section(db: Session, section_id: int, only_active: bool = True) -> Optional[models.Section]:
    """Получает участок по его ID с загрузкой связанных фабрики и оборудования."""
    query = db.query(models.Section).options(
        selectinload(models.Section.factory),
        selectinload(models.Section.equipment)
    ).filter(models.Section.id == section_id)
    if only_active:
        query = query.filter(models.Section.is_active == True)
    return query.first()

def get_section_by_name_and_factory(db: Session, name: str, factory_id: int, only_active: bool = True) -> Optional[models.Section]:
    """Получает участок по наименованию и ID фабрики."""
    query = db.query(models.Section).filter(
        models.Section.name == name,
        models.Section.factory_id == factory_id
    )
    if only_active:
        query = query.filter(models.Section.is_active == True)
    return query.first()

def get_sections(db: Session, skip: int = 0, limit: int = 100, only_active: bool = True) -> List[models.Section]:
    """Получает список участков с пагинацией."""
    query = db.query(models.Section)
    if only_active:
        query = query.filter(models.Section.is_active == True)
    return query.order_by(models.Section.id).offset(skip).limit(limit).all()

def create_section(db: Session, section_data: schemas.SectionCreate) -> models.Section:
    """Создаёт новый участок с привязкой к фабрике и оборудованию."""
    factory = _get_active_entity(db, models.Factory, section_data.factory_id)
    if not factory:
        raise RelatedEntityNotFoundError(f'Активная фабрика с ID {section_data.factory_id} не найдена.')
    if get_section_by_name_and_factory(db, section_data.name, section_data.factory_id, only_active=True):
        raise DuplicateError(f'Активный участок с наименованием "{section_data.name}" уже существует на фабрике ID {section_data.factory_id}.')
    db_section = models.Section(
        name=section_data.name,
        factory_id=section_data.factory_id,
        is_active=True
    )
    found_equipment = []
    missing_or_inactive_equipment_ids = []
    if section_data.equipment_ids:
        for eq_id in section_data.equipment_ids:
            equipment_item = _get_active_entity(db, models.Equipment, eq_id)
            if equipment_item:
                found_equipment.append(equipment_item)
            else:
                missing_or_inactive_equipment_ids.append(eq_id)
        if missing_or_inactive_equipment_ids:
            raise RelatedEntityNotFoundError(f'Активное оборудование с ID {missing_or_inactive_equipment_ids} не найдено.')
        db_section.equipment.extend(found_equipment)
    db.add(db_section)
    db.commit()
    db.refresh(db_section)
    return db_section

def update_section(db: Session, section_id: int, section_data: schemas.SectionUpdate) -> models.Section:
    """Обновляет данные активного участка."""
    db_section = _get_active_entity(db, models.Section, section_id)
    if not db_section:
        raise NotFoundError(f'Активный участок с ID {section_id} не найден.')
    target_factory_id = db_section.factory_id
    if section_data.factory_id is not None and section_data.factory_id != db_section.factory_id:
        new_factory = _get_active_entity(db, models.Factory, section_data.factory_id)
        if not new_factory:
            raise RelatedEntityNotFoundError(f'Новая активная фабрика с ID {section_data.factory_id} не найдена.')
        target_factory_id = new_factory.id
        db_section.factory_id = new_factory.id
    target_name = db_section.name
    if section_data.name is not None:
        target_name = section_data.name
    if (section_data.name is not None and section_data.name != db_section.name) or \
       (section_data.factory_id is not None and section_data.factory_id != db_section.factory_id):
        existing_section = get_section_by_name_and_factory(db, target_name, target_factory_id, only_active=True)
        if existing_section and existing_section.id != section_id:
            raise DuplicateError(f'Активный участок с наименованием "{target_name}" уже существует на фабрике ID {target_factory_id}.')
    if section_data.name is not None:
        db_section.name = section_data.name
    if section_data.equipment_ids is not None:
        new_equipment_list = []
        missing_or_inactive_equipment_ids = []
        if section_data.equipment_ids:
            for eq_id in section_data.equipment_ids:
                equipment_item = _get_active_entity(db, models.Equipment, eq_id)
                if equipment_item:
                    new_equipment_list.append(equipment_item)
                else:
                    missing_or_inactive_equipment_ids.append(eq_id)
            if missing_or_inactive_equipment_ids:
                raise RelatedEntityNotFoundError(f'Активное оборудование с ID {missing_or_inactive_equipment_ids} не найдено при обновлении участка.')
        db_section.equipment = new_equipment_list
    db.commit()
    db.refresh(db_section)
    return db_section

def soft_delete_section(db: Session, section_id: int) -> models.Section:
    """Мягко удаляет (деактивирует) участок."""
    db_section = _get_active_entity(db, models.Section, section_id)
    if not db_section:
        raise NotFoundError(f'Активный участок с ID {section_id} не найден.')
    problematic_equipment_names = []
    for eq in db_section.equipment:
        other_active_sections_count = db.query(models.Section).join(models.section_equipment_association_table).filter(
            models.section_equipment_association_table.c.equipment_id == eq.id,
            models.Section.is_active == True,
            models.Section.id != section_id
        ).count()
        if other_active_sections_count == 0:
            problematic_equipment_names.append(eq.name)
    if problematic_equipment_names:
        raise DependentActiveChildError(
            f'Нельзя деактивировать участок ID {section_id}, следующее активное оборудование ({", ".join(problematic_equipment_names)}) останется без других активных участков.'
        )
    db_section.is_active = False
    db.commit()
    db.refresh(db_section)
    return db_section


# --- Иерархия ---

def get_parents_for_equipment(db: Session, equipment_id: int) -> List[schemas.HierarchyParent]:
    """Получает список родительских сущностей для оборудования."""
    parents = []
    equipment = _get_active_entity(db, models.Equipment, equipment_id)
    if not equipment:
        return parents
    processed_factories = set()
    for section in equipment.sections:
        parents.append(schemas.HierarchyParent(type='section', id=section.id, name=section.name))
        if section.factory and section.factory.is_active and section.factory.id not in processed_factories:
            parents.append(schemas.HierarchyParent(type='factory', id=section.factory.id, name=section.factory.name))
            processed_factories.add(section.factory.id)
    return parents

def get_parents_for_section(db: Session, section_id: int) -> List[schemas.HierarchyParent]:
    """Получает список родительских сущностей для участка."""
    parents = []
    section = _get_active_entity(db, models.Section, section_id)
    if not section:
        return parents
    if section.factory and section.factory.is_active:
        parents.append(schemas.HierarchyParent(type='factory', id=section.factory.id, name=section.factory.name))
    return parents

def get_children_for_factory(db: Session, factory_id: int) -> List[schemas.HierarchyChild]:
    """Получает список дочерних сущностей для фабрики."""
    children = []
    factory = _get_active_entity(db, models.Factory, factory_id)
    if not factory:
        return children
    for section in factory.sections:
        section_child = schemas.HierarchyChild(type='section', id=section.id, name=section.name)
        equipment_children = []
        for eq in section.equipment:
            equipment_children.append(schemas.HierarchyChild(type='equipment', id=eq.id, name=eq.name, children=[]))
        section_child.children = equipment_children
        children.append(section_child)
    return children

def get_children_for_section(db: Session, section_id: int) -> List[schemas.HierarchyChild]:
    """Получает список дочерних сущностей для участка."""
    children = []
    section = _get_active_entity(db, models.Section, section_id)
    if not section:
        return children
    for eq in section.equipment:
        children.append(schemas.HierarchyChild(type='equipment', id=eq.id, name=eq.name, children=[]))
    return children

def activate_factory(db: Session, factory_id: int) -> models.Factory:
    """Активирует ранее деактивированную фабрику."""
    db_factory = db.query(models.Factory).filter(models.Factory.id == factory_id).first()
    if not db_factory:
        raise NotFoundError(f'Фабрика с ID {factory_id} не найдена.')
    if db_factory.is_active:
        raise AlreadyActiveError(f'Фабрика с ID {factory_id} уже активна.')
    db_factory.is_active = True
    db.commit()
    db.refresh(db_factory)
    return db_factory

def activate_section(db: Session, section_id: int) -> models.Section:
    """Активирует ранее деактивированный участок."""
    db_section = db.query(models.Section).filter(models.Section.id == section_id).first()
    if not db_section:
        raise NotFoundError(f'Участок с ID {section_id} не найден.')
    if db_section.is_active:
        raise AlreadyActiveError(f'Участок с ID {section_id} уже активен.')
    db_section.is_active = True
    db.commit()
    db.refresh(db_section)
    return db_section

def activate_equipment(db: Session, equipment_id: int) -> models.Equipment:
    """Активирует ранее деактивированное оборудование."""
    db_equipment = db.query(models.Equipment).filter(models.Equipment.id == equipment_id).first()
    if not db_equipment:
        raise NotFoundError(f'Оборудование с ID {equipment_id} не найдено.')
    if db_equipment.is_active:
        raise AlreadyActiveError(f'Оборудование с ID {equipment_id} уже активно.')
    db_equipment.is_active = True
    db.commit()
    db.refresh(db_equipment)
    return db_equipment
