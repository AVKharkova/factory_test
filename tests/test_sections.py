from fastapi.testclient import TestClient
from fastapi import status


def test_create_section(client: TestClient):
    """Тест создания участка с привязкой оборудования."""
    factory_response = client.post(
        "/factories/", json={"name": "Фабрика для Участков"}
    )
    assert factory_response.status_code == status.HTTP_201_CREATED
    factory_id = factory_response.json()["id"]

    eq1_res = client.post(
        "/equipment/", json={"name": "Оборудование А для Участка", "section_ids": []}
    )
    eq2_res = client.post(
        "/equipment/", json={"name": "Оборудование Б для Участка", "section_ids": []}
    )
    assert eq1_res.status_code == status.HTTP_201_CREATED
    assert eq2_res.status_code == status.HTTP_201_CREATED
    eq1_id = eq1_res.json()["id"]
    eq2_id = eq2_res.json()["id"]

    section_data = {
        "name": "Новый Участок Тест",
        "factory_id": factory_id,
        "equipment_ids": [eq1_id, eq2_id]
    }
    response = client.post("/sections/", json=section_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Новый Участок Тест"
    assert data["factory_id"] == factory_id
    assert data["is_active"] is True


def test_create_section_invalid_factory(client: TestClient):
    """Тест создания участка с несуществующей фабрикой."""
    section_data = {
        "name": "Участок с неверной фабрикой",
        "factory_id": 99999,
        "equipment_ids": []
    }
    response = client.post("/sections/", json=section_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Активная фабрика" in response.json()["detail"]
    assert "не найдена" in response.json()["detail"]


def test_create_section_invalid_equipment(client: TestClient):
    """Тест создания участка с несуществующим оборудованием."""
    factory_response = client.post(
        "/factories/", json={"name": "Фабрика для Ошибочного Участка"}
    )
    factory_id = factory_response.json()["id"]

    section_data = {
        "name": "Участок с неверным оборудованием",
        "factory_id": factory_id,
        "equipment_ids": [99901, 99902]
    }
    response = client.post("/sections/", json=section_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Активное оборудование" in response.json()["detail"]
    assert "не найдено" in response.json()["detail"]


def test_read_one_section_with_details(client: TestClient):
    """Тест получения участка с деталями (фабрика, оборудование)."""
    factory_res = client.post(
        "/factories/", json={"name": "Фабрика для деталей участка"}
    )
    factory_id = factory_res.json()["id"]
    eq_res = client.post(
        "/equipment/", json={"name": "Обор. для деталей участка"}
    )
    eq_id = eq_res.json()["id"]
    section_create_res = client.post(
        "/sections/",
        json={"name": "Участок с деталями", "factory_id": factory_id, "equipment_ids": [eq_id]}
    )
    section_id = section_create_res.json()["id"]

    response = client.get(f"/sections/{section_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == section_id
    assert data["name"] == "Участок с деталями"
    assert data["factory"]["id"] == factory_id
    assert data["factory"]["name"] == "Фабрика для деталей участка"
    assert len(data["equipment"]) == 1
    assert data["equipment"][0]["id"] == eq_id
    assert data["equipment"][0]["name"] == "Обор. для деталей участка"


def test_update_section(client: TestClient):
    """Тест обновления участка."""
    factory_res = client.post(
        "/factories/", json={"name": "Фабрика для обновления"}
    )
    factory_id = factory_res.json()["id"]
    new_factory_res = client.post(
        "/factories/", json={"name": "Новая Фабрика для обновления"}
    )
    new_factory_id = new_factory_res.json()["id"]
    eq_res = client.post(
        "/equipment/", json={"name": "Оборудование для обновления"}
    )
    eq_id = eq_res.json()["id"]

    section_create_res = client.post(
        "/sections/",
        json={"name": "Участок для обновления", "factory_id": factory_id, "equipment_ids": [eq_id]}
    )
    section_id = section_create_res.json()["id"]

    update_data = {
        "name": "Обновленный Участок",
        "factory_id": new_factory_id,
        "equipment_ids": []
    }
    response = client.put(f"/sections/{section_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Обновленный Участок"
    assert data["factory_id"] == new_factory_id
    assert len(data["equipment"]) == 0


def test_delete_section(client: TestClient):
    """Тест мягкого удаления участка."""
    factory_res = client.post(
        "/factories/", json={"name": "Фабрика для удаления"}
    )
    factory_id = factory_res.json()["id"]
    section_create_res = client.post(
        "/sections/",
        json={"name": "Участок для удаления", "factory_id": factory_id, "equipment_ids": []}
    )
    section_id = section_create_res.json()["id"]

    response = client.delete(f"/sections/{section_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["is_active"] is False

    get_response = client.get(f"/sections/{section_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_activate_section(client: TestClient):
    """Тест активации участка."""
    factory_res = client.post(
        "/factories/", json={"name": "Фабрика для активации"}
    )
    factory_id = factory_res.json()["id"]
    section_create_res = client.post(
        "/sections/",
        json={"name": "Участок для активации", "factory_id": factory_id, "equipment_ids": []}
    )
    section_id = section_create_res.json()["id"]

    client.delete(f"/sections/{section_id}")

    response = client.put(f"/sections/{section_id}/activate")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["is_active"] is True

    get_response = client.get(f"/sections/{section_id}")
    assert get_response.status_code == status.HTTP_200_OK
    assert get_response.json()["is_active"] is True


def test_soft_delete_section_with_dependent_equipment(client: TestClient):
    """Тест удаления участка с зависимым оборудованием."""
    factory_res = client.post(
        "/factories/", json={"name": "Фабрика с зависимым оборудованием"}
    )
    factory_id = factory_res.json()["id"]
    section_create_res = client.post(
        "/sections/",
        json={"name": "Участок с зависимым оборудованием", "factory_id": factory_id, "equipment_ids": []}
    )
    section_id = section_create_res.json()["id"]
    eq_res = client.post(
        "/equipment/",
        json={"name": "Зависимое Оборудование", "section_ids": [section_id]}
    )
    assert eq_res.status_code == status.HTTP_201_CREATED

    response = client.delete(f"/sections/{section_id}")
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "активное оборудование" in response.json()["detail"]
    assert "без других активных участков" in response.json()["detail"]
