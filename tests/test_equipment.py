from fastapi.testclient import TestClient
from fastapi import status

def test_create_equipment(client: TestClient):
    # 1. Создаем фабрику и участок
    factory_res = client.post(
        "/factories/",
        json={"name": "Фабрика для оборудования"}
    )
    factory_id = factory_res.json()["id"]
    section_res = client.post(
        "/sections/",
        json={
            "name": "Участок для оборудования",
            "factory_id": factory_id,
            "equipment_ids": []
        }
    )
    section_id = section_res.json()["id"]

    # 2. Создаем оборудование
    equipment_data = {
        "name": "Новое Оборудование Тест",
        "description": "Описание тестового оборудования",
        "section_ids": [section_id]
    }
    response = client.post("/equipment/", json=equipment_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Новое Оборудование Тест"
    assert data["description"] == "Описание тестового оборудования"

    # Проверка связи (получаем оборудование по ID)
    get_response = client.get(f"/equipment/{data['id']}")
    full_data = get_response.json()
    assert len(full_data["sections"]) == 1
    assert full_data["sections"][0]["id"] == section_id
