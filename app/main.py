from fastapi import FastAPI, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from sqlalchemy.orm import Session

from .database import get_db
from .routers import factories, sections, equipment, hierarchy
from .exceptions import (
    NotFoundError,
    DuplicateError,
    RelatedEntityNotFoundError,
)

app = FastAPI(title='Справочники API')
app.mount('/static', StaticFiles(directory='app/static'), name='static')


# Подключение роутеров
app.include_router(factories.router)
app.include_router(sections.router)
app.include_router(equipment.router)
app.include_router(hierarchy.router)


# Обработчики исключений
@app.exception_handler(NotFoundError)
async def not_found_error_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={'detail': str(exc)})


@app.exception_handler(DuplicateError)
async def duplicate_error_handler(request: Request, exc: DuplicateError):
    return JSONResponse(status_code=400, content={'detail': str(exc)})


@app.exception_handler(RelatedEntityNotFoundError)
async def related_entity_error_handler(request: Request, exc: RelatedEntityNotFoundError):
    return JSONResponse(status_code=400, content={'detail': str(exc)})


# Иконка, чтобы не надоедал с ошибкой
@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse('app/static/favicon.ico')

# HTML интерфейс
html_content = '''
<!DOCTYPE html>
<html>
<head>
    <title>Справочники</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f4; color: #333; }
        .container { background-color: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        h1, h2 { color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }
        form { margin-bottom: 30px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; background-color: #f9f9f9; }
        label { display: block; margin-top: 10px; font-weight: bold; }
        input[type="text"], input[type="number"], select {
            margin-top: 5px;
            width: calc(100% - 22px);
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 4px;
            box-sizing: border-box;
        }
        button {
            margin-top: 15px;
            padding: 10px 15px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover { background-color: #45a049; }
        .hierarchy-result { margin-top: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; background-color: #e9f5e9; }
        pre { background-color: #eee; padding: 10px; border-radius: 4px; overflow-x: auto; }
    </style>
    <script>
        async function submitHierarchyForm(event) {
            event.preventDefault();
            const form = event.target;
            const entityType = form.entity_type.value;
            const entityId = form.entity_id.value;
            const responseDisplay = document.getElementById('hierarchy_response');
            responseDisplay.innerHTML = '<p>Загрузка...</p>';

            try {
                const response = await fetch(`/hierarchy/?entity_type=${entityType}&entity_id=${entityId}`);
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(`Ошибка ${response.status}: ${errorData.detail || 'Не удалось получить данные'}`);
                }
                const data = await response.json();
                responseDisplay.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
            } catch (error) {
                responseDisplay.innerHTML = '<p style="color: red;">' + error.message + '</p>';
            }
        }
    </script>
</head>
<body>
    <div class="container">
        <h1>Управление справочниками</h1>

        <h2>Создать Фабрику</h2>
        <form action="/factories/" method="post" target="response_iframe">
            <label for="factory_name">Наименование фабрики:</label>
            <input type="text" id="factory_name" name="name" required>
            <button type="submit">Создать</button>
        </form>

        <h2>Создать Участок</h2>
        <form action="/sections/" method="post" target="response_iframe">
            <label for="section_name">Наименование участка:</label>
            <input type="text" id="section_name" name="name" required>
            <label for="factory_id_section">ID фабрики:</label>
            <input type="number" id="factory_id_section" name="factory_id" required>
            <label for="equipment_ids_section">ID оборудования (через запятую, например: 1,2,3):</label>
            <input type="text" id="equipment_ids_section" name="equipment_ids" placeholder="1,2,3">
            <button type="submit">Создать</button>
        </form>

        <h2>Создать Оборудование</h2>
        <form action="/equipment/" method="post" target="response_iframe">
            <label for="equipment_name">Наименование оборудования:</label>
            <input type="text" id="equipment_name" name="name" required>
            <label for="equipment_description">Описание оборудования (опционально):</label>
            <input type="text" id="equipment_description" name="description">
            <label for="section_ids_equipment">ID участков (через запятую, например: 1,2,3):</label>
            <input type="text" id="section_ids_equipment" name="section_ids" placeholder="1,2,3">
            <button type="submit">Создать</button>
        </form>

        <h2>Получить иерархию</h2>
        <form onsubmit="submitHierarchyForm(event)">
            <label for="entity_type">Тип сущности:</label>
            <select id="entity_type" name="entity_type">
                <option value="factory">Фабрика</option>
                <option value="section">Участок</option>
                <option value="equipment">Оборудование</option>
            </select>
            <label for="entity_id">ID сущности:</label>
            <input type="number" id="entity_id" name="entity_id" required>
            <button type="submit">Получить</button>
        </form>
        <div id="hierarchy_response" class="hierarchy-result"></div>

        <h2>Ответ сервера (для форм создания):</h2>
        <iframe name="response_iframe" style="width:100%; height:150px; border:1px solid #ccc;"></iframe>
    </div>
</body>
</html>
'''


@app.get('/', response_class=HTMLResponse, tags=['UI'])
async def get_ui_form():
    """HTML-интерфейс для управления справочниками."""
    return HTMLResponse(content=html_content)


@app.get('/ping', tags=['Health'])
async def ping():
    """Проверка доступности API."""
    return {'message': 'pong'}
