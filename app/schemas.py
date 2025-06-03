from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class FactoryBase(BaseModel):
    id: Optional[int] = Field(None, description='ID Фабрики')
    name: str = Field(..., description='Наименование фабрики')
    model_config = ConfigDict(from_attributes=True)


class SectionBase(BaseModel):
    id: Optional[int] = Field(None, description='ID Участка')
    name: str = Field(..., description='Наименование участка')
    model_config = ConfigDict(from_attributes=True)


class EquipmentBase(BaseModel):
    id: Optional[int] = Field(None, description='ID Оборудования')
    name: str = Field(..., description='Наименование оборудования')
    description: Optional[str] = Field(None, description='Описание оборудования')
    model_config = ConfigDict(from_attributes=True)


class FactoryCreate(FactoryBase):
    id: Optional[int] = Field(None, exclude=True)


class SectionCreate(SectionBase):
    id: Optional[int] = Field(None, exclude=True)
    factory_id: int = Field(..., description='ID фабрики участка')
    equipment_ids: Optional[List[int]] = Field(
        default_factory=list,
        description='Список ID оборудования для привязки'
    )


class EquipmentCreate(EquipmentBase):
    id: Optional[int] = Field(None, exclude=True)
    section_ids: Optional[List[int]] = Field(
        default_factory=list,
        description='Список ID участков для привязки'
    )


class FactoryUpdate(BaseModel):
    name: Optional[str] = Field(None, description='Новое наименование фабрики')


class SectionUpdate(BaseModel):
    name: Optional[str] = Field(None, description='Новое наименование участка')
    factory_id: Optional[int] = Field(None, description='Новый ID фабрики')
    equipment_ids: Optional[List[int]] = Field(
        None,
        description='Новый список ID оборудования'
    )


class EquipmentUpdate(BaseModel):
    name: Optional[str] = Field(None, description='Новое наименование оборудования')
    description: Optional[str] = Field(None, description='Новое описание')
    section_ids: Optional[List[int]] = Field(
        None,
        description='Новый список ID участков'
    )


class Factory(FactoryBase):
    id: int = Field(..., description='ID фабрики')
    is_active: bool = Field(..., description='Флаг активности')
    sections: List[SectionBase] = Field(
        default_factory=list,
        description='Список активных участков'
    )


class Section(SectionBase):
    id: int = Field(..., description='ID участка')
    factory_id: int = Field(..., description='ID фабрики')
    is_active: bool = Field(..., description='Флаг активности')
    equipment: List[EquipmentBase] = Field(
        default_factory=list,
        description='Список активного оборудования'
    )


class Equipment(EquipmentBase):
    id: int = Field(..., description='ID оборудования')
    is_active: bool = Field(..., description='Флаг активности')
    sections: List[SectionBase] = Field(
        default_factory=list,
        description='Список активных участков'
    )


class FactoryFull(Factory):
    pass


class SectionFull(Section):
    factory: FactoryBase = Field(..., description='Фабрика участка')


class EquipmentFull(Equipment):
    pass


class HierarchyParent(BaseModel):
    type: str = Field(..., description='Тип объекта')
    id: int = Field(..., description='ID объекта')
    name: str = Field(..., description='Наименование объекта')
    model_config = ConfigDict(from_attributes=True)


class HierarchyChild(BaseModel):
    type: str = Field(..., description='Тип объекта')
    id: int = Field(..., description='ID объекта')
    name: str = Field(..., description='Наименование объекта')
    children: Optional[List['HierarchyChild']] = Field(
        None,
        description='Список дочерних объектов'
    )
    model_config = ConfigDict(from_attributes=True)


class HierarchyResponse(BaseModel):
    entity_type: str = Field(..., description='Тип объекта')
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
    model_config = ConfigDict(from_attributes=True)


HierarchyChild.model_rebuild()
