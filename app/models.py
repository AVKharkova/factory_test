from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, Table, Boolean, and_
)
from sqlalchemy.orm import relationship

from .database import Base

# Таблица связи "участок — оборудование"
section_equipment_association_table = Table(
    'section_equipment_association',
    Base.metadata,
    Column(
        'section_id',
        Integer,
        ForeignKey('sections.id'),
        primary_key=True,
        doc='Внешний ключ к таблице участков'
    ),
    Column(
        'equipment_id',
        Integer,
        ForeignKey('equipment.id'),
        primary_key=True,
        doc='Внешний ключ к таблице оборудования'
    )
)


class Factory(Base):
    """Модель Фабрики."""
    __tablename__ = 'factories'

    id = Column(Integer, primary_key=True, index=True, doc='Айди фабрики')
    name = Column(String, unique=True, index=True, nullable=False, doc='Наименование фабрики')
    is_active = Column(Boolean, default=True, nullable=False, index=True, doc='Флаг активности записи')

    sections = relationship(
        'Section', 
        back_populates='factory',
        cascade='all, delete-orphan',
        primaryjoin=lambda: and_(Factory.id == Section.factory_id, Section.is_active == True),
        doc='Участки, принадлежащие фабрике'
    )


class Section(Base):
    """Модель Участка."""
    __tablename__ = 'sections'

    id = Column(Integer, primary_key=True, index=True, doc='Айди участка')
    name = Column(String, index=True, nullable=False, doc='Наименование участка')
    factory_id = Column(Integer, ForeignKey('factories.id'), nullable=False, doc='Внешний ключ к фабрике')
    is_active = Column(Boolean, default=True, nullable=False, index=True, doc='Флаг активности записи')

    factory = relationship(
        'Factory',
        back_populates='sections',
        doc='Фабрика, к которой относится участок'
    )

    equipment = relationship(
        'Equipment',
        secondary=section_equipment_association_table,
        back_populates='sections',
        primaryjoin=lambda: Section.id == section_equipment_association_table.c.section_id,
        secondaryjoin=lambda: and_(
            section_equipment_association_table.c.equipment_id == Equipment.id,
            Equipment.is_active == True
        ),
        doc='Оборудование, находящееся на данном участке'
    )


class Equipment(Base):
    """Модель Оборудования."""
    __tablename__ = 'equipment'

    id = Column(Integer, primary_key=True, index=True, doc='Айди оборудования')
    name = Column(String, unique=True, index=True, nullable=False, doc='Наименование оборудования')
    description = Column(Text, nullable=True, doc='Описание оборудования')
    is_active = Column(Boolean, default=True, nullable=False, index=True, doc='Флаг активности записи')

    sections = relationship(
        'Section',
        secondary=section_equipment_association_table,
        back_populates='equipment',
        primaryjoin=lambda: Equipment.id == section_equipment_association_table.c.equipment_id,
        secondaryjoin=lambda: and_(
            section_equipment_association_table.c.section_id == Section.id,
            Section.is_active == True
        ),
        doc='Участки, на которых находится оборудование'
    )
