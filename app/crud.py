from sqlalchemy.orm import Session, joinedload, selectinload
from . import models, schemas
from .exceptions import NotFoundError, RelatedEntityNotFoundError, DuplicateError
from typing import List, Optional

# --- Операции CRUD для фабрик ---
def get_factory(db: Session, factory_id: int) -> Optional[models.Factory]:
    """Получает фабрику по её id."""
    return db.query(models.Factory).filter(models.Factory.id == factory_id).first()


def get_factory_by_name(db: Session, name: str) -> Optional[models.Factory]:
    """Получает фабрику по её наименованию."""
    return db.query(models.Factory).filter(models.Factory.name == name).first()


def get_factories(db: Session, skip: int = 0, limit: int = 100) -> List[models.Factory]:
    """Получает список фабрик с пагинацией."""
    return db.query(models.Factory).offset(skip).limit(limit).all()


def create_factory(db: Session, factory_data: schemas.FactoryCreate) -> models.Factory:
    """Создаёт новую фабрику. """
    if get_factory_by_name(db, factory_data.name):
        raise DuplicateError(f"Фабрика с наименованием '{factory_data.name}' уже существует.")
    db_factory = models.Factory(name=factory_data.name)
    db.add(db_factory)
    db.commit()
    db.refresh(db_factory)
    return db_factory


def update_factory(db: Session, factory_id: int, factory_data: schemas.FactoryUpdate) -> Optional[models.Factory]:
    """Обновляет фабрику."""
    db_factory = get_factory(db, factory_id)
    if not db_factory:
        raise NotFoundError(f"Фабрика с id {factory_id} не найдена.")

    if factory_data.name is not None and factory_data.name != db_factory.name:
        existing_factory = get_factory_by_name(db, factory_data.name)
        if existing_factory and existing_factory.id != factory_id:
            raise DuplicateError(f"Фабрика с наименованием '{factory_data.name}' уже существует.")
        db_factory.name = factory_data.name

    db.commit()
    db.refresh(db_factory)
    return db_factory


def delete_factory(db: Session, factory_id: int) -> Optional[models.Factory]:
    """Удаляет фабрику. """
    db_factory = get_factory(db, factory_id)
    if not db_factory:
        raise NotFoundError(f"Фабрика с id {factory_id} не найдена.")
    db.delete(db_factory)
    db.commit()
    return db_factory


# --- Операции CRUD для оборудования ---
def get_equipment(db: Session, equipment_id: int) -> Optional[models.Equipment]:
    """Получает оборудование по его id."""
    return db.query(models.Equipment).options(selectinload(models.Equipment.sections)).filter(models.Equipment.id == equipment_id).first()


def get_equipment_by_name(db: Session, name: str) -> Optional[models.Equipment]:
    """Получает оборудование по его наименованию."""
    return db.query(models.Equipment).filter(models.Equipment.name == name).first()


def get_equipment_list(db: Session, skip: int = 0, limit: int = 100) -> List[models.Equipment]:
    """Получает список оборудования с пагинацией."""
    return db.query(models.Equipment).offset(skip).limit(limit).all()


def create_equipment(db: Session, equipment_data: schemas.EquipmentCreate) -> models.Equipment:
    """Создаёт новое оборудование и связывает его с указанными участками. """
    if get_equipment_by_name(db, equipment_data.name):
        raise DuplicateError(f"Оборудование с наименованием '{equipment_data.name}' уже существует.")

    db_equipment = models.Equipment(name=equipment_data.name, description=equipment_data.description)
    
    found_sections = []
    missing_section_ids = []
    if equipment_data.section_ids:
        for section_id in equipment_data.section_ids:
            section = get_section(db, section_id)
            if section:
                found_sections.append(section)
            else:
                missing_section_ids.append(section_id)
        
        if missing_section_ids:
            raise RelatedEntityNotFoundError(f"Участки с id {missing_section_ids} не найдены.")
        db_equipment.sections.extend(found_sections)

    db.add(db_equipment)
    db.commit()
    db.refresh(db_equipment)
    return db_equipment


def update_equipment(db: Session, equipment_id: int, equipment_data: schemas.EquipmentUpdate) -> Optional[models.Equipment]:
    """Обновляет оборудование."""
    db_equipment = get_equipment(db, equipment_id)
    if not db_equipment:
        raise NotFoundError(f"Оборудование с id {equipment_id} не найдено.")

    if equipment_data.name is not None and equipment_data.name != db_equipment.name:
        existing_equipment = get_equipment_by_name(db, equipment_data.name)
        if existing_equipment and existing_equipment.id != equipment_id:
            raise DuplicateError(f"Оборудование с наименованием '{equipment_data.name}' уже существует.")
        db_equipment.name = equipment_data.name
    
    if equipment_data.description is not None:
        db_equipment.description = equipment_data.description

    if equipment_data.section_ids is not None: 
        new_sections = []
        missing_section_ids = []
        if equipment_data.section_ids:
            for section_id in equipment_data.section_ids:
                section = get_section(db, section_id)
                if section:
                    new_sections.append(section)
                else:
                    missing_section_ids.append(section_id)
            
            if missing_section_ids:
                raise RelatedEntityNotFoundError(f"Участки с id {missing_section_ids} не найдены при обновлении оборудования.")
        
        db_equipment.sections = new_sections  # Заменяем список участков

    db.commit()
    db.refresh(db_equipment)
    return db_equipment


def delete_equipment(db: Session, equipment_id: int) -> Optional[models.Equipment]:
    """Удаляет оборудование."""
    db_equipment = get_equipment(db, equipment_id)
    if not db_equipment:
        raise NotFoundError(f"Оборудование с id {equipment_id} не найдено.")
    db.delete(db_equipment)
    db.commit()
    return db_equipment


# --- Операции CRUD для участков ---
def get_section(db: Session, section_id: int) -> Optional[models.Section]:
    """Получает участок по его id."""
    return db.query(models.Section).options(
        selectinload(models.Section.factory), 
        selectinload(models.Section.equipment)
    ).filter(models.Section.id == section_id).first()


def get_section_by_name_and_factory(db: Session, name: str, factory_id: int) -> Optional[models.Section]:
    """Получает участок по имени и id фабрики."""
    return db.query(models.Section).filter(models.Section.name == name, models.Section.factory_id == factory_id).first()


def get_sections(db: Session, skip: int = 0, limit: int = 100) -> List[models.Section]:
    """Получает список участков с пагинацией."""
    return db.query(models.Section).offset(skip).limit(limit).all()


def create_section(db: Session, section_data: schemas.SectionCreate) -> models.Section:
    """Создаёт новый участок и связывает его с фабрикой и оборудованием."""
    factory = get_factory(db, section_data.factory_id)
    if not factory:
        raise RelatedEntityNotFoundError(f"Фабрика с id {section_data.factory_id} не найдена.")

    if get_section_by_name_and_factory(db, section_data.name, section_data.factory_id):
        raise DuplicateError(f"Участок с наименованием '{section_data.name}' уже существует на фабрике id {section_data.factory_id}.")

    db_section = models.Section(name=section_data.name, factory_id=section_data.factory_id)
    
    found_equipment = []
    missing_equipment_ids = []
    if section_data.equipment_ids:
        for eq_id in section_data.equipment_ids:
            equipment_item = get_equipment(db, eq_id)
            if equipment_item:
                found_equipment.append(equipment_item)
            else:
                missing_equipment_ids.append(eq_id)
        
        if missing_equipment_ids:
            raise RelatedEntityNotFoundError(f"Оборудование с id {missing_equipment_ids} не найдено.")
        db_section.equipment.extend(found_equipment)

    db.add(db_section)
    db.commit()
    db.refresh(db_section)
    return db_section


def update_section(db: Session, section_id: int, section_data: schemas.SectionUpdate) -> Optional[models.Section]:
    """Обновляет участок."""
    db_section = get_section(db, section_id)
    if not db_section:
        raise NotFoundError(f"Участок с id {section_id} не найден.")

    target_factory_id = db_section.factory_id
    if section_data.factory_id is not None and section_data.factory_id != db_section.factory_id:
        new_factory = get_factory(db, section_data.factory_id)
        if not new_factory:
            raise RelatedEntityNotFoundError(f"Новая фабрика с id {section_data.factory_id} не найдена.")
        target_factory_id = new_factory.id
        db_section.factory_id = new_factory.id

    target_name = db_section.name
    if section_data.name is not None and section_data.name != db_section.name:
        target_name = section_data.name
    
    if (section_data.name is not None and section_data.name != db_section.name) or \
       (section_data.factory_id is not None and section_data.factory_id != db_section.factory_id):
        existing_section = get_section_by_name_and_factory(db, target_name, target_factory_id)
        if existing_section and existing_section.id != section_id:
            raise DuplicateError(f"Участок с наименованием '{target_name}' уже существует на фабрике id {target_factory_id}.")
    
    if section_data.name is not None:
        db_section.name = section_data.name

    if section_data.equipment_ids is not None:
        new_equipment_list = []
        missing_equipment_ids = []
        if section_data.equipment_ids:
            for eq_id in section_data.equipment_ids:
                equipment_item = get_equipment(db, eq_id)
                if equipment_item:
                    new_equipment_list.append(equipment_item)
                else:
                    missing_equipment_ids.append(eq_id)
            
            if missing_equipment_ids:
                raise RelatedEntityNotFoundError(f"Оборудование с id {missing_equipment_ids} не найдено при обновлении участка.")
        
        db_section.equipment = new_equipment_list  # Заменяем список оборудования

    db.commit()
    db.refresh(db_section)
    return db_section


def delete_section(db: Session, section_id: int) -> Optional[models.Section]:
    """Удаляет участок."""
    db_section = get_section(db, section_id)
    if not db_section:
        raise NotFoundError(f"Участок с id {section_id} не найден.")
    db.delete(db_section)
    db.commit()
    return db_section


def get_parents_for_equipment(db: Session, equipment_id: int) -> List[schemas.HierarchyParent]:
    """Получает всех родительских объектов для оборудования (участки и фабрики)."""
    parents = []
    equipment = db.query(models.Equipment).options(
        selectinload(models.Equipment.sections).selectinload(models.Section.factory)
    ).filter(models.Equipment.id == equipment_id).first()
    
    if not equipment:
        return parents

    # Родители 0-го уровня: участки
    processed_factories = set()  # уникальность
    for section in equipment.sections:
        parents.append(schemas.HierarchyParent(type='section', id=section.id, name=section.name))
        # Родители 1-го уровня: фабрика участка
        if section.factory and section.factory.id not in processed_factories:
            parents.append(
                schemas.HierarchyParent(type='factory', id=section.factory.id, name=section.factory.name))
            processed_factories.add(section.factory.id)
    return parents


def get_parents_for_section(db: Session, section_id: int) -> List[schemas.HierarchyParent]:
    """Получает всех родительских объектов для участка (фабрика)."""
    parents = []
    # Используем selectinload для фабрики
    section = db.query(models.Section).options(selectinload(models.Section.factory)).filter(
        models.Section.id == section_id).first()
    
    if not section:
        return parents

    # Родитель 0-го уровня: фабрика
    if section.factory:
        parents.append(schemas.HierarchyParent(type='factory', id=section.factory.id, name=section.factory.name))
    return parents


def _get_equipment_for_sections(db: Session, section_ids: List[int]) -> List[schemas.HierarchyChild]:
    """Вспомогательная функция: получает оборудование, связанное с указанными участками.
    Эта функция не используется в текущей логике иерархии, но может быть полезна.
    """
    children_equipment = []
    if not section_ids:
        return children_equipment
        
    equipment_list = db.query(models.Equipment) \
        .join(models.section_equipment_association_table) \
        .filter(models.section_equipment_association_table.c.section_id.in_(section_ids)) \
        .distinct().all()

    for eq in equipment_list:
        children_equipment.append(schemas.HierarchyChild(type='equipment', id=eq.id, name=eq.name, children=[]))
    return children_equipment


def get_children_for_factory(db: Session, factory_id: int) -> List[schemas.HierarchyChild]:
    """Получает всех дочерних объектов для фабрики (участки и оборудование)."""
    children = []
    factory = db.query(models.Factory).options(
        selectinload(models.Factory.sections).selectinload(models.Section.equipment)
    ).filter(models.Factory.id == factory_id).first()
    
    if not factory:
        return children

    # Дети 0-го уровня: Участки
    for section in factory.sections:
        section_child = schemas.HierarchyChild(type='section', id=section.id, name=section.name)
        # Дети 1-го уровня (дети участка) оборудование
        equipment_children = []
        if section.equipment:
            for eq in section.equipment:
                equipment_children.append(schemas.HierarchyChild(type='equipment', id=eq.id, name=eq.name, children=[]))
        section_child.children = equipment_children
        children.append(section_child)
    return children


def get_children_for_section(db: Session, section_id: int) -> List[schemas.HierarchyChild]:
    """Получает всех дочерних объектов для участка (оборудование)."""
    children = []
    section = db.query(models.Section).options(selectinload(models.Section.equipment)).filter(
        models.Section.id == section_id).first()

    if not section:
        return children

    # Дети 0-го уровня: Оборудование
    if section.equipment:
        for eq in section.equipment:
            children.append(schemas.HierarchyChild(type='equipment', id=eq.id, name=eq.name, children=[]))
    return children
