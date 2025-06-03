import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import get_db, Base
from app.main import app as fastapi_app
import app.models  # для регистрации моделей в Base.metadata

from alembic.config import Config
from alembic import command
import os

SQLALCHEMY_DATABASE_URL_TEST = "sqlite:///./test_spravochniki.db"

ALEMBIC_INI_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    ),
    "alembic.ini"
)

engine_test = create_engine(
    SQLALCHEMY_DATABASE_URL_TEST,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine_test
)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

fastapi_app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    """
    Фикстура для применения Alembic миграций к тестовой БД перед
    запуском сессии тестов и удаления тестовой БД после.
    """
    db_file_path = SQLALCHEMY_DATABASE_URL_TEST.replace(
        "sqlite:///", ""
    )
    if os.path.exists(db_file_path):
        print(
            f"Удаляю старую тестовую базу данных: {db_file_path}"
        )
        os.remove(db_file_path)

    print(
        f"Актуализирую настройки Alembic: {ALEMBIC_INI_PATH} и БД: "
        f"{SQLALCHEMY_DATABASE_URL_TEST}"
    )

    alembic_cfg = Config(ALEMBIC_INI_PATH)
    alembic_cfg.set_main_option(
        "sqlalchemy.url", SQLALCHEMY_DATABASE_URL_TEST
    )

    print("Применяю Alembic-миграции к тестовой базе данных...")
    try:
        command.upgrade(alembic_cfg, "head")
        print(
            "Alembic-миграции успешно применены к тестовой базе данных."
        )
    except Exception as e:
        print(f"Ошибка при применении Alembic-миграций: {e}")
        raise

    yield

@pytest.fixture(scope="session")
def client(apply_migrations):
    """
    Фикстура для создания TestClient.
    Зависит от фикстуры apply_migrations, чтобы БД была готова.
    """
    from fastapi.testclient import TestClient
    with TestClient(fastapi_app) as c:
        yield c
