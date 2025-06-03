from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import subprocess
import os

from app.routers import factories, sections, equipment, hierarchy
from app.exceptions import (
    NotFoundError,
    DuplicateError,
    RelatedEntityNotFoundError,
    DependentActiveChildError,
    AlreadyInactiveError,
    AlreadyActiveError,
)
import app.models  # Чтобы Alembic видел модели

ALEMBIC_INI_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "alembic.ini"
)

@asynccontextmanager
async def lifespan(app_: FastAPI):
    """Автоматический запуск Alembic миграций при старте приложения."""
    if os.path.exists(ALEMBIC_INI_PATH):
        project_root = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
        proc = subprocess.run(
            ["alembic", "-c", ALEMBIC_INI_PATH, "upgrade", "head"],
            capture_output=True,
            text=True,
            check=False,
            cwd=project_root
        )
        if proc.returncode != 0:
            print("Alembic migration failed.")
            print(proc.stdout)
            print(proc.stderr)
    else:
        print("alembic.ini not found, skipping migrations.")
    yield

app = FastAPI(title='Справочники API', lifespan=lifespan)
app.mount('/static', StaticFiles(directory='app/static'), name='static')
templates = Jinja2Templates(directory='app/templates')

# Подключение роутеров
app.include_router(factories.router)
app.include_router(sections.router)
app.include_router(equipment.router)
app.include_router(hierarchy.router)

# Обработчики исключений
@app.exception_handler(NotFoundError)
async def not_found_error_handler(request: Request, exc: NotFoundError):
    """Обработчик для исключения NotFoundError."""
    return JSONResponse(
        status_code=404, content={'detail': str(exc)}
    )

@app.exception_handler(DuplicateError)
async def duplicate_error_handler(request: Request, exc: DuplicateError):
    """Обработчик для исключения DuplicateError."""
    return JSONResponse(
        status_code=400, content={'detail': str(exc)}
    )

@app.exception_handler(RelatedEntityNotFoundError)
async def related_entity_error_handler(
    request: Request, exc: RelatedEntityNotFoundError
):
    """Обработчик для RelatedEntityNotFoundError."""
    return JSONResponse(
        status_code=400, content={'detail': str(exc)}
    )

@app.exception_handler(DependentActiveChildError)
async def dependent_active_child_error_handler(
    request: Request, exc: DependentActiveChildError
):
    """Обработчик для DependentActiveChildError."""
    return JSONResponse(
        status_code=409, content={'detail': str(exc)}
    )

@app.exception_handler(AlreadyInactiveError)
async def already_inactive_error_handler(
    request: Request, exc: AlreadyInactiveError
):
    """Обработчик для AlreadyInactiveError."""
    return JSONResponse(
        status_code=400, content={'detail': str(exc)}
    )

@app.exception_handler(AlreadyActiveError)
async def already_active_error_handler(
    request: Request, exc: AlreadyActiveError
):
    """Обработчик для AlreadyActiveError."""
    return JSONResponse(
        status_code=400, content={'detail': str(exc)}
    )

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    """Возвращает favicon.ico."""
    return FileResponse('app/static/favicon.ico')

@app.get('/', tags=['UI'])
async def get_ui_form(request: Request):
    """HTML-интерфейс для управления справочниками."""
    return templates.TemplateResponse('index.html', {'request': request})

@app.get('/ping', tags=['Health'])
async def ping():
    """Проверка доступности API."""
    return {'message': 'pong'}
