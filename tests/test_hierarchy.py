from fastapi.testclient import TestClient
from fastapi import status


def test_get_hierarchy_for_factory(client: TestClient):
    """Тест получения иерархии для фабрики."""
    f_res = client.post("/factories/", json={"name": "Фабрика для Иерархии"})
    f_id = f_res.json()["id"]
    s_res = client.post(
        "/sections/",
        json={"name": "Участок для Иерархии Ф", "factory_id": f_id, "equipment_ids": []}
    )
    s_id = s_res.json()["id"]
    e_res = client.post(
        "/equipment/",
        json={"name": "Обор. для Иерархии Ф", "section_ids": [s_id]}
    )
    e_id = e_res.json()["id"]

    response = client.get(f"/hierarchy/?entity_type=factory&entity_id={f_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["entity_id"] == f_id
    assert data["entity_name"] == "Фабрика для Иерархии"
    assert len(data["parents"]) == 0
    assert len(data["children"]) == 1
    assert data["children"][0]["type"] == "section"
    assert data["children"][0]["id"] == s_id
    assert len(data["children"][0]["children"]) == 1
    assert data["children"][0]["children"][0]["type"] == "equipment"
    assert data["children"][0]["children"][0]["id"] == e_id


def test_get_hierarchy_for_section(client: TestClient):
    """Тест получения иерархии для участка."""
    f_res = client.post("/factories/", json={"name": "Фабрика для Иерархии С"})
    f_id = f_res.json()["id"]
    s_res = client.post(
        "/sections/",
        json={"name": "Участок для Иерархии С", "factory_id": f_id, "equipment_ids": []}
    )
    s_id = s_res.json()["id"]
    e_res = client.post(
        "/equipment/",
        json={"name": "Обор. для Иерархии С", "section_ids": [s_id]}
    )
    e_id = e_res.json()["id"]

    response = client.get(f"/hierarchy/?entity_type=section&entity_id={s_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["entity_id"] == s_id
    assert data["entity_name"] == "Участок для Иерархии С"
    assert len(data["parents"]) == 1
    assert data["parents"][0]["type"] == "factory"
    assert data["parents"][0]["id"] == f_id
    assert len(data["children"]) == 1
    assert data["children"][0]["type"] == "equipment"
    assert data["children"][0]["id"] == e_id


def test_get_hierarchy_for_equipment(client: TestClient):
    """Тест получения иерархии для оборудования."""
    f_res = client.post("/factories/", json={"name": "Фабрика для Иерархии Е"})
    f_id = f_res.json()["id"]
    s_res = client.post(
        "/sections/",
        json={"name": "Участок для Иерархии Е", "factory_id": f_id, "equipment_ids": []}
    )
    s_id = s_res.json()["id"]
    e_res = client.post(
        "/equipment/",
        json={"name": "Обор. для Иерархии Е", "section_ids": [s_id]}
    )
    e_id = e_res.json()["id"]

    response = client.get(f"/hierarchy/?entity_type=equipment&entity_id={e_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["entity_id"] == e_id
    assert data["entity_name"] == "Обор. для Иерархии Е"
    assert len(data["parents"]) == 2
    assert data["parents"][0]["type"] == "section"
    assert data["parents"][0]["id"] == s_id
    assert data["parents"][1]["type"] == "factory"
    assert data["parents"][1]["id"] == f_id
    assert len(data["children"]) == 0