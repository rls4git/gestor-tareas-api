"""Tests para la función get_db() de aplicacion/base_de_datos.py."""

from unittest.mock import patch, MagicMock

from sqlalchemy.orm import Session

from aplicacion.base_de_datos import get_db


def test_get_db_yields_valid_session():
    """Verifica que get_db() devuelve un generador que produce una sesión válida."""
    gen = get_db()
    db = next(gen)
    assert isinstance(db, Session)
    gen.close()


def test_get_db_closes_session_on_normal_exit():
    """Verifica que la sesión se cierra correctamente al terminar el generador."""
    mock_session = MagicMock(spec=Session)
    with patch("aplicacion.base_de_datos.SessionLocal", return_value=mock_session):
        gen = get_db()
        db = next(gen)
        assert db is mock_session
        gen.close()
    mock_session.close.assert_called_once()


def test_get_db_closes_session_on_exception():
    """Verifica que la sesión se cierra incluso si ocurre una excepción."""
    mock_session = MagicMock(spec=Session)
    with patch("aplicacion.base_de_datos.SessionLocal", return_value=mock_session):
        gen = get_db()
        db = next(gen)
        assert db is mock_session
        try:
            gen.throw(RuntimeError("error simulado"))
        except RuntimeError:
            pass
    mock_session.close.assert_called_once()
