from typing import List, Optional

from pydantic import BaseModel, Field

# --- Схемы для оборудования ---

class EquipmentBase(BaseModel):
    name: str = Field(..., description='Наименование оборудования')
    description: Optional[str] = Field(
        None,
        description='Описание оборудования (опционально)'
    )


class EquipmentCreate(EquipmentBase):
    section_ids: Optional[List[int]] = Field(
        default_factory=list,
        description='Список ID участков для привязки оборудования при создании'
    )


class EquipmentUpdate(BaseModel):
    name: Optional[str] = Field(None, description='Новое наименование оборудования')
    description: Optional[str] = Field(None, description='Новое описание оборудования')
    section_ids: Optional[List[int]] = Field(
        None,
        description='Новый список ID участков. Передайте [] для удаления всех связей.'
    )


class Equipment(EquipmentBase):
    id: int = Field(..., description='ID оборудования')

    class Config:
        from_attributes = True


class EquipmentFull(Equipment):
    sections: List['SectionBase'] = Field(
        default_factory=list,
        description='Список участков, к которым привязано оборудование'
    )


# --- Схемы для участков ---

class SectionBase(BaseModel):
    name: str = Field(..., description='Наименование участка')


class SectionCreate(SectionBase):
    factory_id: int = Field(..., description='ID фабрики')
    equipment_ids: Optional[List[int]] = Field(
        default_factory=list,
        description='Список ID оборудования для первоначальной привязки'
    )


class SectionUpdate(BaseModel):
    name: Optional[str] = Field(None, description='Новое наименование участка')
    factory_id: Optional[int] = Field(None, description='Новый ID фабрики')
    equipment_ids: Optional[List[int]] = Field(
        None,
        description='Новый список ID оборудования. Передайте [] для удаления всех связей.'
    )


class Section(SectionBase):
    id: int = Field(..., description='ID участка')
    factory_id: int = Field(..., description='ID фабрики')
    equipment: List[EquipmentBase] = Field(
        default_factory=list,
        description='Список оборудования, привязанного к участку'
    )

    class Config:
        from_attributes = True


class SectionFull(Section):
    factory: 'FactoryBase' = Field(..., description='Фабрика, к которой принадлежит участок')
    equipment: List[EquipmentBase] = Field(
        default_factory=list,
        description='Список оборудования'
    )


# --- Схемы для фабрик ---

class FactoryBase(BaseModel):
    name: str = Field(..., description='Наименование фабрики')


class FactoryCreate(FactoryBase):
    pass


class FactoryUpdate(BaseModel):
    name: Optional[str] = Field(None, description='Новое наименование фабрики')


class Factory(FactoryBase):
    id: int = Field(..., description='ID фабрики')
    sections: List[SectionBase] = Field(
        default_factory=list,
        description='Список участков, принадлежащих фабрике'
    )

    class Config:
        from_attributes = True


class FactoryFull(Factory):
    sections: List[SectionBase] = Field(
        default_factory=list,
        description='Список участков'
    )


# --- Схемы для иерархии ---

class HierarchyParent(BaseModel):
    type: str = Field(..., description='Тип объекта (например, "factory", "section")')
    id: int = Field(..., description='ID объекта')
    name: str = Field(..., description='Наименование объекта')


class HierarchyChild(BaseModel):
    type: str = Field(..., description='Тип объекта (например, "section", "equipment")')
    id: int = Field(..., description='ID объекта')
    name: str = Field(..., description='Наименование объекта')
    children: Optional[List['HierarchyChild']] = Field(
        None,
        description='Список дочерних объектов (опционально)'
    )


class HierarchyResponse(BaseModel):
    entity_type: str = Field(..., description='Тип объекта ("factory", "section", "equipment")')
    entity_id: int = Field(..., description='ID объекта')
    entity_name: str = Field(..., description='Наименование объекта')
    parents: List[HierarchyParent] = Field(
        default_factory=list,
        description='Список родительских объектов'
    )
    children: List[HierarchyChild] = Field(
        default_factory=list,
        description='Список дочерних объектов'
    )


# --- Поддержка рекурсивной модели ---
HierarchyChild.model_rebuild()
