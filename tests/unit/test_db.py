"""Testes unitários para db.py - SessionDAO."""

from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, MagicMock, patch, call
import pytest

from oraculo_bot.db import SessionDAO
from oraculo_bot.models import DiscordSession


# Patch global para SUPABASE_DB_URL em todos os testes
@pytest.fixture(autouse=True)
def mock_supabase_db_url(mocker):
    """Mock SUPABASE_DB_URL para evitar usar DB real."""
    mocker.patch("oraculo_bot.db.SUPABASE_DB_URL", None)
    yield


class TestSessionDAOInit:
    """Testes para inicialização do SessionDAO."""

    def test_init_with_url(self):
        """Deve inicializar com db_url fornecido."""
        dao = SessionDAO(db_url="postgresql://test_url")
        assert dao.db_url == "postgresql://test_url"
        assert dao.enabled is True
        assert dao._engine is None
        assert dao._memory_store == {}

    def test_init_without_url(self):
        """Deve aceitar None como db_url."""
        dao = SessionDAO(db_url=None)
        assert dao.db_url is None
        assert dao.enabled is False

    def test_init_uses_default_when_supabase_set(self, mocker):
        """Deve usar SUPABASE_DB_URL do config quando db_url não fornecido."""
        mocker.patch("oraculo_bot.db.SUPABASE_DB_URL", "postgresql://default")
        dao = SessionDAO()  # Sem db_url
        assert dao.db_url == "postgresql://default"


class TestSessionDAOEnabled:
    """Testes para property enabled."""

    def test_enabled_true_with_url(self):
        """Deve retornar True se db_url configurado."""
        dao = SessionDAO(db_url="postgresql://test")
        assert dao.enabled is True

    def test_enabled_false_without_url(self):
        """Deve retornar False se sem db_url."""
        dao = SessionDAO(db_url=None)
        # Garante que enabled é False quando db_url é None
        assert dao.db_url is None
        assert dao.enabled is False


class TestSessionDAOMemoryStore:
    """Testes para fallback de memória."""

    def test_create_session_in_memory(self):
        """Deve criar sessão na memória quando DB desabilitado."""
        dao = SessionDAO(db_url=None)

        result = dao.create_session("thread1", "user1", "estudo")

        assert result.thread_id == "thread1"
        assert result.user_id == "user1"
        assert result.mode == "estudo"
        assert "thread1" in dao._memory_store

    def test_get_session_from_memory(self):
        """Deve recuperar da memória."""
        dao = SessionDAO(db_url=None)
        session = DiscordSession(
            thread_id="thread1",
            user_id="user1",
            mode="estudo",
            session_data={}
        )
        dao._memory_store["thread1"] = session

        result = dao.get_session("thread1")

        assert result is session
        assert result.thread_id == "thread1"

    def test_get_session_not_found_in_memory(self):
        """Deve retornar None se não está na memória."""
        dao = SessionDAO(db_url=None)

        result = dao.get_session("nonexistent")

        assert result is None

    def test_update_session_data_in_memory(self):
        """Deve atualizar na memória."""
        dao = SessionDAO(db_url=None)
        session = DiscordSession(
            thread_id="thread1",
            user_id="user1",
            mode="estudo",
            session_data={"old": "data"}
        )
        dao._memory_store["thread1"] = session

        result = dao.update_session_data("thread1", {"new": "value"})

        assert result.session_data == {"old": "data", "new": "value"}

    def test_update_session_data_not_found_in_memory(self):
        """Deve retornar None se sessão não existe na memória."""
        dao = SessionDAO(db_url=None)

        result = dao.update_session_data("nonexistent", {"key": "value"})

        assert result is None

    def test_get_or_create_in_memory_returns_existing(self):
        """Deve retornar existente da memória."""
        dao = SessionDAO(db_url=None)
        existing = DiscordSession(
            thread_id="thread1",
            user_id="user1",
            mode="estudo",
            session_data={}
        )
        dao._memory_store["thread1"] = existing

        result = dao.get_or_create_session("thread1", "user1", "casual")

        assert result is existing
        assert result.mode == "estudo"  # Mantém mode existente

    def test_get_or_create_in_memory_creates_new(self):
        """Deve criar nova na memória."""
        dao = SessionDAO(db_url=None)

        result = dao.get_or_create_session("thread1", "user1", "professor")

        assert result.thread_id == "thread1"
        assert result.mode == "professor"
        assert "thread1" in dao._memory_store

    def test_cleanup_old_sessions_in_memory(self):
        """Deve retornar 0 quando usando memória."""
        dao = SessionDAO(db_url=None)

        count = dao.cleanup_old_sessions(days=30)

        assert count == 0

    def test_memory_store_isolated_between_instances(self):
        """Deve isolar memória entre instâncias."""
        dao1 = SessionDAO(db_url=None)
        dao2 = SessionDAO(db_url=None)

        session1 = DiscordSession(
            thread_id="thread1",
            user_id="user1",
            mode="estudo",
            session_data={}
        )
        dao1._memory_store["thread1"] = session1

        # DAO2 não deve ver a sessão do DAO1
        assert "thread1" not in dao2._memory_store


class TestSessionDAOEdgeCases:
    """Testes de edge cases para SessionDAO."""

    def test_empty_session_data_update_in_memory(self):
        """Deve lidar com atualização de dados vazios na memória."""
        dao = SessionDAO(db_url=None)
        session = DiscordSession(
            thread_id="thread1",
            user_id="user1",
            mode="estudo",
            session_data={"existing": "data"}
        )
        dao._memory_store["thread1"] = session

        result = dao.update_session_data("thread1", {})

        # Dados existentes devem ser mantidos
        assert result.session_data == {"existing": "data"}

    def test_session_data_merge_nested_dicts_in_memory(self):
        """Deve mergir corretamente dicts na memória."""
        dao = SessionDAO(db_url=None)
        session = DiscordSession(
            thread_id="thread1",
            user_id="user1",
            mode="estudo",
            session_data={"config": {"theme": "dark"}}
        )
        dao._memory_store["thread1"] = session

        result = dao.update_session_data("thread1", {"config": {"lang": "pt"}})

        # Nota: update() substitui a chave inteira, não merge profundo
        assert result.session_data["config"]["lang"] == "pt"

    def test_concurrent_get_or_create_in_memory(self):
        """Deve lidar com múltiplas chamadas na memória."""
        dao = SessionDAO(db_url=None)

        # Simular múltiplas chamadas
        results = [dao.get_or_create_session("thread1", "user1") for _ in range(5)]

        # Todas devem retornar sessões válidas
        assert all(r.thread_id == "thread1" for r in results)
        # Todas devem ser a mesma instância
        assert len(set(id(r) for r in results)) == 1


class TestDiscordSessionModel:
    """Testes para o modelo DiscordSession."""

    def test_discord_session_creation(self):
        """Deve criar sessão com valores padrão."""
        session = DiscordSession(
            thread_id="thread123",
            user_id="user123",
            mode="estudo",
            session_data={}  # SQLAlchemy não usa default no construtor
        )

        assert session.thread_id == "thread123"
        assert session.user_id == "user123"
        assert session.mode == "estudo"
        assert session.session_data == {}
        # Timestamps são criados pelo SQLAlchemy, não no construtor
        # assert isinstance(session.created_at, datetime)
        # assert isinstance(session.updated_at, datetime)

    def test_discord_session_with_custom_data(self):
        """Deve criar sessão com dados customizados."""
        session = DiscordSession(
            thread_id="thread123",
            user_id="user123",
            mode="professor",
            session_data={"history": [], "config": {"theme": "dark"}}
        )

        assert session.mode == "professor"
        assert session.session_data["history"] == []
        assert session.session_data["config"]["theme"] == "dark"

    def test_discord_session_repr(self):
        """Deve ter representação legível."""
        session = DiscordSession(
            thread_id="thread123",
            user_id="user123",
            mode="estudo"
        )

        repr_str = repr(session)
        assert "thread123" in repr_str
        assert "user123" in repr_str
        assert "estudo" in repr_str
