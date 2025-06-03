from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = 'sqlite:///./spravochniki.db'

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        'check_same_thread': False
    } if SQLALCHEMY_DATABASE_URL.startswith('sqlite') else {}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    """Зависимость FastAPI для получения сессии базы данных."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
