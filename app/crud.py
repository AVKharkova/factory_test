from sqlalchemy.orm import Session, joinedload
from . import models, schemas
from typing import List, Optional

# --- Операции CRUD для фабрик ---
def get_factory(db: Session, factory_id: int) -> Optional[models.Factory]:
    """Получает фабрику по её ID."""
    return db.query(models.Factory).filter(models.Factory.id == factory_id).first()


def get_factory_by_name(db: Session, name: str) -> Optional[models.Factory]:
    """Получает фабрику по её наименованию."""
    return db.query(models.Factory).filter(models.Factory.name == name).first()


def get_factories(db: Session, skip: int = 0, limit: int = 100) -> List[models.Factory]:
    """Получает список фабрик с пагинацией."""
    return db.query(models.Factory).offset(skip).limit(limit).all()


def create_factory(db: Session, factory: schemas.FactoryCreate) -> models.Factory:
    """Создаёт новую фабрику."""
    db_factory = models.Factory(name=factory.name)
    db.add(db_factory)
    db.commit()
    db.refresh(db_factory)
    return db_factory


# --- Операции CRUD для оборудования ---
def get_equipment(db: Session, equipment_id: int) -> Optional[models.Equipment]:
    """Получает оборудование по его ID."""
    return db.query(models.Equipment).filter(models.Equipment.id == equipment_id).first()


def get_equipment_by_name(db: Session, name: str) -> Optional[models.Equipment]:
    """Получает оборудование по его наименованию."""
    return db.query(models.Equipment).filter(models.Equipment.name == name).first()


def get_equipment_list(db: Session, skip: int = 0, limit: int = 100) -> List[models.Equipment]:
    """Получает список оборудования с пагинацией."""
    return db.query(models.Equipment).offset(skip).limit(limit).all()


def create_equipment(db: Session, equipment: schemas.EquipmentCreate) -> models.Equipment:
    """Создаёт новое оборудование и связывает его с указанными участками."""
    db_equipment = models.Equipment(name=equipment.name, description=equipment.description)

    # Связываем с участками, если IDs предоставлены
    if equipment.section_ids:
        for section_id in equipment.section_ids:
            section = get_section(db, section_id)
            if section:
                db_equipment.sections.append(section)
            else:
                print(f'Предупреждение: участок с id {section_id} не найден при создании оборудования.')

    db.add(db_equipment)
    db.commit()
    db.refresh(db_equipment)
    return db_equipment


# --- Операции CRUD для участков ---
def get_section(db: Session, section_id: int) -> Optional[models.Section]:
    """Получает участок по его ID."""
    return db.query(models.Section).filter(models.Section.id == section_id).first()


def get_sections(db: Session, skip: int = 0, limit: int = 100) -> List[models.Section]:
    """Получает список участков с пагинацией."""
    return db.query(models.Section).offset(skip).limit(limit).all()


def create_section(db: Session, section: schemas.SectionCreate) -> Optional[models.Section]:
    """Создаёт новый участок и связывает его с фабрикой и оборудованием."""
    factory = get_factory(db, section.factory_id)
    if not factory:
        return None

    db_section = models.Section(name=section.name, factory_id=section.factory_id)

    # Связываем с оборудованием, если IDs предоставлены
    if section.equipment_ids:
        for eq_id in section.equipment_ids:
            equipment_item = get_equipment(db, eq_id)
            if equipment_item:
                db_section.equipment.append(equipment_item)
            else:
                print(f'Предупреждение: Оборудование с id {eq_id} не найдено при создании участка.')

    db.add(db_section)
    db.commit()
    db.refresh(db_section)
    return db_section


# --- Логика иерархии ---
def get_parents_for_equipment(db: Session, equipment_id: int) -> List[schemas.HierarchyParent]:
    """Получает всех родительских объектов для оборудования (участки и фабрики)."""
    parents = []
    equipment = db.query(models.Equipment).options(
        joinedload(models.Equipment.sections).joinedload(models.Section.factory)).filter(
        models.Equipment.id == equipment_id).first()
    if not equipment:
        return parents

    # Родители 0-го уровня: участки
    processed_sections = set()
    for section in equipment.sections:
        if section.id not in processed_sections:
            parents.append(schemas.HierarchyParent(type='section', id=section.id, name=section.name))
            processed_sections.add(section.id)
            # Родители 1-го уровня: фабрика участка
            if section.factory:
                # Уникальность
                factory_already_added = any(p.type == 'factory' and p.id == section.factory.id for p in parents)
                if not factory_already_added:
                    parents.append(
                        schemas.HierarchyParent(type='factory', id=section.factory.id, name=section.factory.name))
    return parents


def get_parents_for_section(db: Session, section_id: int) -> List[schemas.HierarchyParent]:
    """Получает всех родительских объектов для участка (фабрика)."""
    parents = []
    section = db.query(models.Section). clarifiedoptions(joinedload(models.Section.factory)).filter(
        models.Section.id == section_id).first()
    if not section or not section.factory:
        return parents

    # Родитель 0-го уровня: фабрика
    parents.append(schemas.HierarchyParent(type='factory', id=section.factory.id, name=section.factory.name))
    return parents


def _get_equipment_for_sections(db: Session, section_ids: List[int]) -> List[schemas.HierarchyChild]:
    """Получает оборудование, связанное с указанными участками (вспомогательная функция). """
    children_equipment = []
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
    factory = db.query(models.Factory).options(joinedload(models.Factory.sections)).filter(
        models.Factory.id == factory_id).first()
    if not factory:
        return children

    # Дети 0-го уровня: Участки
    for section in factory.sections:
        section_child = schemas.HierarchyChild(type='section', id=section.id, name=section.name)
        # Дети 1-го уровня (дети участка): Оборудование
        equipment_children = []
        for eq in section.equipment:
            equipment_children.append(schemas.HierarchyChild(type='equipment', id=eq.id, name=eq.name, children=[]))
        section_child.children = equipment_children
        children.append(section_child)
    return children


def get_children_for_section(db: Session, section_id: int) -> List[schemas.HierarchyChild]:
    """Получает всех дочерних объектов для участка (оборудование). """
    children = []
    section = db.query(models.Section).options(joinedload(models.Section.equipment)).filter(
        models.Section.id == section_id).first()
    if not section:
        return children

    # Дети 0-го уровня: Оборудование
    for eq in section.equipment:
        children.append(schemas.HierarchyChild(type='equipment', id=eq.id, name=eq.name, children=[]))
    return children
