from fastapi.testclient import TestClient

from app.main import create_app


def make_client(tmp_path):
    app = create_app(f"sqlite:///{tmp_path / 'test.db'}")
    return TestClient(app)


def test_create_task_and_persist_after_new_request(tmp_path):
    with make_client(tmp_path) as client:
        response = client.post("/tasks", data={"title": "Купить молоко", "current_filter": "all"})
        assert response.status_code == 200
        assert "Купить молоко" in response.text

        response = client.get("/")
        assert response.status_code == 200
        assert "Купить молоко" in response.text
        assert "Активных задач: 1" in response.text


def test_empty_task_is_rejected(tmp_path):
    with make_client(tmp_path) as client:
        response = client.post("/tasks", data={"title": "   ", "current_filter": "all"})
        assert response.status_code == 422
        assert "Введите текст задачи" in response.text
        assert "Задач здесь пока нет" in response.text


def test_toggle_and_filter_task(tmp_path):
    with make_client(tmp_path) as client:
        client.post("/tasks", data={"title": "Готовая задача", "current_filter": "all"})
        response = client.post("/tasks/1/toggle", data={"current_filter": "all"})
        assert response.status_code == 200
        assert 'class="task completed"' in response.text
        assert "Всё сделано" in response.text

        response = client.get("/?filter=active")
        assert "Готовая задача" not in response.text
        response = client.get("/?filter=completed")
        assert "Готовая задача" in response.text


def test_edit_and_delete_task(tmp_path):
    with make_client(tmp_path) as client:
        client.post("/tasks", data={"title": "Черновик", "current_filter": "all"})
        response = client.post("/tasks/1/edit", data={"title": "Финальная задача", "current_filter": "all"})
        assert response.status_code == 200
        assert "Финальная задача" in response.text
        assert "Черновик" not in response.text

        response = client.post("/tasks/1/delete", data={"current_filter": "all"})
        assert response.status_code == 200
        assert "Задач здесь пока нет" in response.text
