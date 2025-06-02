from pydantic import BaseModel, Field
from typing import List, Optional

class EquipmentBase(BaseModel):
    """Базовая схема для оборудования."""
    name: str = Field(..., description='Наименование оборудования')
    description: Optional[str] = Field(None, description='Описание оборудования (опционально)')


class EquipmentCreate(EquipmentBase):
    """Схема для создания оборудования."""
    section_ids: Optional[List[int]] = Field(
        default_factory=list,
        description='Список ID участков для привязки оборудования при создании'
    )


class Equipment(EquipmentBase):
    """Схема для представления оборудования с ID и связями."""
    id: int = Field(..., description='Айди оборудования')

    class Config:
        from_attributes = True


class SectionBase(BaseModel):
    """Базовая схема для участка."""
    name: str = Field(..., description='Наименование участка')


class SectionCreate(SectionBase):
    """Схема для создания участка."""
    factory_id: int = Field(..., description='ID фабрики, к которой принадлежит участок')
    equipment_ids: Optional[List[int]] = Field(
        default_factory=list,
        description='Опциональный список ID оборудования для первоначальной привязки'
    )


class Section(SectionBase):
    """Схема для представления участка с ID, фабрикой и оборудованием."""
    id: int = Field(..., description='Айди участка')
    factory_id: int = Field(..., description='Айди фабрики, к которой принадлежит участок')
    equipment: List[EquipmentBase] = Field(
        default=[],
        description='Список базовой информации об оборудовании, привязанном к участку'
    )

    class Config:
        from_attributes = True


# --- Схемы для фабрик ---
class FactoryBase(BaseModel):
    """Базовая схема для фабрики."""
    name: str = Field(..., description='Наименование фабрики')


class FactoryCreate(FactoryBase):
    """Схема для создания фабрики."""
    pass


class Factory(FactoryBase):
    """Схема для представления фабрики с ID и участками."""
    id: int = Field(..., description='Уникальный идентификатор фабрики')
    sections: List[SectionBase] = Field(
        default=[],
        description='Список базовой информации об участках, принадлежащих фабрике'
    )

    class Config:
        from_attributes = True


class EquipmentFull(Equipment):
    """Полная схема оборудования с привязанными участками."""
    sections: List[SectionBase] = Field(
        default=[],
        description='Список базовой информации об участках, к которым привязано оборудование'
    )


class SectionFull(Section):
    """Полная схема участка с фабрикой и оборудованием."""
    factory: FactoryBase = Field(..., description='Базовая информация о фабрике')
    equipment: List[EquipmentBase] = Field(
        default=[],
        description='Список базовой информации об оборудовании'
    )


class FactoryFull(Factory):
    """Полная схема фабрики с участками."""
    sections: List[SectionBase] = Field(
        default=[],
        description='Список базовой информации об участках'
    )


# --- Схемы для иерархии ---
class HierarchyParent(BaseModel):
    """Схема для представления родительского объекта в иерархии."""
    type: str = Field(..., description='Тип объекта (например, "factory" или "section")')
    id: int = Field(..., description='Уникальный идентификатор объекта')
    name: str = Field(..., description='Наименование объекта')


class HierarchyChild(BaseModel):
    """Схема для представления дочернего объекта в иерархии с рекурсией."""
    type: str = Field(..., description='Тип объекта (например, "section" или "equipment")')
    id: int = Field(..., description='Уникальный идентификатор объекта')
    name: str = Field(..., description='Наименование объекта')
    children: Optional[List['HierarchyChild']] = Field(
        None,
        description='Рекурсивный список дочерних объектов (опционально)'
    )


# Pydantic V2: model_rebuild() для рекурсивных моделей
# HierarchyChild.model_rebuild()


class HierarchyResponse(BaseModel):
    """Схема ответа для представления иерархии объекта."""
    entity_type: str = Field(..., description='Тип объекта ("factory", "section", "equipment")')
    entity_id: int = Field(..., description='Уникальный идентификатор объекта')
    entity_name: str = Field(..., description='Наименование объекта')
    parents: List[HierarchyParent] = Field(
        default=[],
        description='Список родительских объектов'
    )
    children: List[HierarchyChild] = Field(
        default=[],
        description='Список дочерних объектов'
    )
