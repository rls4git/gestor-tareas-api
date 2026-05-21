from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aplicacion.base_de_datos import Base, get_db
from aplicacion.principal import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_tareas.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_module():
    Base.metadata.create_all(bind=engine)


def teardown_module():
    Base.metadata.drop_all(bind=engine)


def test_create_task_title_too_short_returns_422():
    response = client.post("/tasks/", json={"title": "ab"})
    assert response.status_code == 422


def test_list_tasks_by_status_returns_matching_tasks():
    client.post("/tasks/", json={"title": "Pendiente uno"})
    client.post("/tasks/", json={"title": "Pendiente dos"})
    done_resp = client.post("/tasks/", json={"title": "Tarea hecha"})
    task_id = done_resp.json()["id"]
    client.patch(f"/tasks/{task_id}", json={"status": "done"})

    response = client.get("/tasks/status/done")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(t["id"] == task_id and t["status"] == "done" for t in data)


def test_list_tasks_by_status_invalid_returns_422():
    response = client.get("/tasks/status/invalid")
    assert response.status_code == 422
