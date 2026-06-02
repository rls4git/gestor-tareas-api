"""Tests del lifespan de la aplicación para cubrir líneas 14-15 de principal.py."""

from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.pool import StaticPool

from aplicacion.base_de_datos import Base
from aplicacion.principal import app, lifespan

# Motor en memoria aislado de la BD de producción
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(autouse=True)
def clean_tables():
    """Elimina las tablas antes y después de cada test para garantizar aislamiento."""
    Base.metadata.drop_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.mark.anyio
async def test_lifespan_executes_successfully():
    """Verifica que el lifespan se ejecuta sin errores al inicializar la app."""
    with patch("aplicacion.principal.engine", test_engine):
        async with lifespan(app):
            inspector = inspect(test_engine)
            table_names = inspector.get_table_names()
            assert len(table_names) > 0


@pytest.mark.anyio
async def test_lifespan_creates_tasks_table():
    """Verifica que la tabla 'tasks' se crea al arrancar el lifespan."""
    inspector = inspect(test_engine)
    assert inspector.get_table_names() == []

    with patch("aplicacion.principal.engine", test_engine):
        async with lifespan(app):
            inspector = inspect(test_engine)
            assert "tasks" in inspector.get_table_names()
