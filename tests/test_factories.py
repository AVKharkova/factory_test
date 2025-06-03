from fastapi.testclient import TestClient
from fastapi import status


def test_create_factory(client: TestClient):
    """Тест создания фабрики."""
    response = client.post("/factories/", json={"name": "Новая Фабрика Тест"})
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Новая Фабрика Тест"
    assert data["is_active"] is True
    assert "id" in data


def test_create_duplicate_factory(client: TestClient):
    """Тест создания дубликата фабрики."""
    client.post("/factories/", json={"name": "Дубликат Фабрика"})
    response = client.post("/factories/", json={"name": "Дубликат Фабрика"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "уже существует" in response.json()["detail"]


def test_read_factories_empty(client: TestClient):
    """Тест проверки отсутствия активных фабрик после деактивации."""
    response_before = client.get("/factories/")
    assert response_before.status_code == status.HTTP_200_OK
    initial_count = len(response_before.json())

    create_res = client.post(
        "/factories/", json={"name": "Test Empty Check Factory"}
    )
    assert create_res.status_code == status.HTTP_201_CREATED
    new_factory_id = create_res.json()["id"]

    response_after_create = client.get("/factories/")
    assert response_after_create.status_code == status.HTTP_200_OK
    assert len(response_after_create.json()) == initial_count + 1

    delete_res = client.delete(f"/factories/{new_factory_id}")
    assert delete_res.status_code == status.HTTP_200_OK

    response_after_delete = client.get("/factories/")
    assert response_after_delete.status_code == status.HTTP_200_OK
    assert len(response_after_delete.json()) == initial_count
    assert not any(f["id"] == new_factory_id for f in response_after_delete.json())


def test_read_factories_with_data(client: TestClient):
    """Тест получения списка фабрик с данными."""
    client.post("/factories/", json={"name": "Фабрика А"})
    client.post("/factories/", json={"name": "Фабрика Б"})

    response = client.get("/factories/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 2
    names = [item["name"] for item in data]
    assert "Фабрика А" in names
    assert "Фабрика Б" in names


def test_read_one_factory(client: TestClient):
    """Тест получения одной фабрики по ID."""
    create_response = client.post(
        "/factories/", json={"name": "Фабрика для Чтения"}
    )
    factory_id = create_response.json()["id"]

    response = client.get(f"/factories/{factory_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == factory_id
    assert data["name"] == "Фабрика для Чтения"


def test_read_one_factory_not_found(client: TestClient):
    """Тест получения несуществующей фабрики."""
    response = client.get("/factories/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_factory(client: TestClient):
    """Тест обновления фабрики."""
    create_response = client.post(
        "/factories/", json={"name": "Старое Имя Фабрики"}
    )
    factory_id = create_response.json()["id"]

    response = client.put(
        f"/factories/{factory_id}", json={"name": "Новое Имя Фабрики"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Новое Имя Фабрики"
    assert data["id"] == factory_id

    get_response = client.get(f"/factories/{factory_id}")
    assert get_response.json()["name"] == "Новое Имя Фабрики"


def test_update_factory_duplicate_name(client: TestClient):
    """Тест обновления фабрики с дублирующим именем."""
    client.post("/factories/", json={"name": "Имя Уже Занято"})
    create_response_2 = client.post(
        "/factories/", json={"name": "Фабрика для Переименования"}
    )
    factory_id_to_rename = create_response_2.json()["id"]

    response = client.put(
        f"/factories/{factory_id_to_rename}", json={"name": "Имя Уже Занято"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "уже существует" in response.json()["detail"]


def test_update_factory_not_found(client: TestClient):
    """Тест обновления несуществующей фабрики."""
    response = client.put("/factories/99999", json={"name": "Неважно"})
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_soft_delete_factory(client: TestClient):
    """Тест мягкого удаления фабрики."""
    create_response = client.post(
        "/factories/", json={"name": "Фабрика для Деактивации"}
    )
    factory_id = create_response.json()["id"]

    delete_response = client.delete(f"/factories/{factory_id}")
    assert delete_response.status_code == status.HTTP_200_OK
    assert delete_response.json()["is_active"] is False

    get_active_response = client.get("/factories/")
    active_factories = get_active_response.json()
    assert not any(f["id"] == factory_id for f in active_factories)

    get_all_response = client.get("/factories/?include_inactive=true")
    all_factories = get_all_response.json()
    assert any(f["id"] == factory_id and not f["is_active"] for f in all_factories)

    get_inactive_by_id_response = client.get(
        f"/factories/{factory_id}?include_inactive=true"
    )
    assert get_inactive_by_id_response.status_code == status.HTTP_200_OK
    assert get_inactive_by_id_response.json()["is_active"] is False

    get_active_by_id_response = client.get(f"/factories/{factory_id}")
    assert get_active_by_id_response.status_code == status.HTTP_404_NOT_FOUND


def test_activate_factory(client: TestClient):
    """Тест активации фабрики."""
    create_response = client.post(
        "/factories/", json={"name": "Фабрика для Активации"}
    )
    factory_id = create_response.json()["id"]
    client.delete(f"/factories/{factory_id}")

    activate_response = client.put(f"/factories/{factory_id}/activate")
    assert activate_response.status_code == status.HTTP_200_OK
    assert activate_response.json()["is_active"] is True

    get_response = client.get(f"/factories/{factory_id}")
    assert get_response.status_code == status.HTTP_200_OK
    assert get_response.json()["is_active"] is True


def test_soft_delete_factory_with_active_sections(client: TestClient):
    """Тест удаления фабрики с активными участками."""
    factory_res = client.post(
        "/factories/", json={"name": "Фабрика с Участками"}
    )
    assert factory_res.status_code == 201
    factory_id = factory_res.json()["id"]

    section_res = client.post(
        "/sections/",
        json={"name": "Активный Участок", "factory_id": factory_id, "equipment_ids": []}
    )
    assert section_res.status_code == 201

    delete_response = client.delete(f"/factories/{factory_id}")
    assert delete_response.status_code == status.HTTP_409_CONFLICT
    assert "активных участков" in delete_response.json()["detail"]
