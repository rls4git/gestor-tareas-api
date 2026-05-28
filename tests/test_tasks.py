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


def test_update_done_task_returns_409():
    response = client.post("/tasks/", json={"title": "Tarea para completar"})
    assert response.status_code == 201
    task_id = response.json()["id"]

    client.patch(f"/tasks/{task_id}", json={"status": "done"})

    response = client.patch(f"/tasks/{task_id}", json={"title": "Nuevo título"})
    assert response.status_code == 409


def test_create_task_description_too_long_returns_422():
    """Verifica que POST /tasks/ devuelve 422 si la descripción supera 500 caracteres."""
    response = client.post(
        "/tasks/", json={"title": "Tarea válida", "description": "x" * 501}
    )
    assert response.status_code == 422


def test_create_task_description_at_max_length_succeeds():
    """Verifica que POST /tasks/ acepta una descripción de exactamente 500 caracteres."""
    response = client.post(
        "/tasks/", json={"title": "Tarea con desc larga", "description": "x" * 500}
    )
    assert response.status_code == 201
    assert len(response.json()["description"]) == 500


def test_update_task_description_too_long_returns_422():
    """Verifica que PATCH /tasks/{id} devuelve 422 si la descripción supera 500 caracteres."""
    response = client.post("/tasks/", json={"title": "Tarea para actualizar"})
    assert response.status_code == 201
    task_id = response.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}", json={"description": "y" * 501}
    )
    assert response.status_code == 422
