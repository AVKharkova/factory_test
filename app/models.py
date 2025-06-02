from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from .database import Base

# Таблица связи Участок-Оборудование
section_equipment_association_table = Table('section_equipment_association', Base.metadata,
    Column('section_id', Integer, ForeignKey('sections.id'), primary_key=True, doc='Внешний ключ к таблице участков'),
    Column('equipment_id', Integer, ForeignKey('equipment.id'), primary_key=True, doc='Внешний ключ к таблице оборудования')
)

class Factory(Base):
    """Модель Фабрики."""
    __tablename__ = 'factories'

    id = Column(Integer, primary_key=True, index=True, doc='Айди фабрики')
    name = Column(String, unique=True, index=True, nullable=False, doc='Наименование фабрики')

    sections = relationship('Section', back_populates='factory', cascade='all, delete-orphan', doc='Участки, принадлежащие этой фабрике')

class Section(Base):
    """Модель Участка."""
    __tablename__ = 'sections'

    id = Column(Integer, primary_key=True, index=True, doc='Айди участка')
    name = Column(String, index=True, nullable=False, doc='Наименование участка (уникально для одной фабрики)')
    factory_id = Column(Integer, ForeignKey('factories.id'), nullable=False, doc='Внешний ключ к фабрике')

    # Связь с фабрикой
    factory = relationship('Factory', back_populates='sections', doc='Фабрика, к которой относится участок')
    # Связь с оборудованием
    equipment = relationship(
        'Equipment',
        secondary=section_equipment_association_table,
        back_populates='sections',
        doc='Оборудование, находящееся на данном участке'
    )

class Equipment(Base):
    """Модель Оборудования."""
    __tablename__ = 'equipment'

    id = Column(Integer, primary_key=True, index=True, doc='Айди оборудования')
    name = Column(String, unique=True, index=True, nullable=False, doc='Наименование оборудования')
    description = Column(Text, nullable=True, doc='Описание оборудования (опционально)')

    # Связь с участками
    sections = relationship(
        'Section',
        secondary=section_equipment_association_table,
        back_populates='equipment',
        doc='Участки, на которых находится оборудование'
    )
