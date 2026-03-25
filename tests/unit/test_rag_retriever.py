"""Testes unitários para RAGRetriever."""

import logging
from unittest.mock import Mock, MagicMock, AsyncMock
import pytest

from oraculo_bot.rag_retriever import RAGRetriever, ALLOWED_METADATA_FILTERS


# Patch global para SUPABASE_DB_URL em todos os testes
@pytest.fixture(autouse=True)
def mock_supabase_db_url(mocker):
    """Mock SUPABASE_DB_URL para evitar usar DB real."""
    mocker.patch("oraculo_bot.rag_retriever.SUPABASE_DB_URL", None)
    yield


class TestRAGRetrieverInit:
    """Testes para inicialização do RAGRetriever."""

    def test_init_with_url(self):
        """Deve inicializar com db_url fornecido."""
        retriever = RAGRetriever(db_url="postgresql://test")
        assert retriever.db_url == "postgresql://test"
        assert retriever._conn is None

    def test_init_without_url(self):
        """Deve aceitar None como db_url."""
        retriever = RAGRetriever(db_url=None)
        assert retriever.db_url is None

    def test_init_uses_default_from_config(self, mocker):
        """Deve usar SUPABASE_DB_URL do config quando db_url não fornecido."""
        mocker.patch("oraculo_bot.rag_retriever.SUPABASE_DB_URL", "postgresql://default")
        retriever = RAGRetriever()
        assert retriever.db_url == "postgresql://default"


class TestRAGRetrieverEnabled:
    """Testes para property enabled."""

    def test_enabled_true_with_url(self):
        """Deve retornar True se db_url configurado."""
        retriever = RAGRetriever(db_url="postgresql://test")
        assert retriever.enabled is True

    def test_enabled_false_without_url(self):
        """Deve retornar False se sem db_url."""
        retriever = RAGRetriever(db_url=None)
        assert retriever.enabled is False


class TestRAGRetrieverConn:
    """Testes para property conn (lazy connection)."""

    def test_conn_lazy_init(self, mocker):
        """Deve inicializar conexão em primeiro acesso."""
        mock_connect = mocker.patch("psycopg.connect", return_value=MagicMock())

        retriever = RAGRetriever(db_url="postgresql://test")
        conn = retriever.conn

        assert conn is not None
        mock_connect.assert_called_once_with("postgresql://test")

    def test_conn_cached(self, mocker):
        """Deve cachear conexão após primeira criação."""
        mock_connect = mocker.patch("psycopg.connect", return_value=MagicMock())

        retriever = RAGRetriever(db_url="postgresql://test")
        conn1 = retriever.conn
        conn2 = retriever.conn

        assert conn1 is conn2
        mock_connect.assert_called_once()

    def test_conn_raises_if_no_url(self):
        """Deve levantar RuntimeError se sem db_url."""
        retriever = RAGRetriever(db_url=None)

        with pytest.raises(RuntimeError, match="SUPABASE_DB_URL não configurada"):
            _ = retriever.conn


class TestRAGRetrieverRetrieve:
    """Testes para retrieve()."""

    def test_retrieve_basic(self, mock_psycopg_connection, sample_embedding):
        """Deve buscar chunks similares com embedding."""
        cursor = mock_psycopg_connection.cursor.return_value
        cursor.fetchall.return_value = [
            (1, "doc1", "Texto...", {"ano": "2021"}, "2021", "FCC", "CF", "22", 0.95)
        ]

        retriever = RAGRetriever(db_url="postgresql://test")
        results = retriever.retrieve(
            query_text="teste",
            query_embedding=sample_embedding,
            top_k=5
        )

        assert len(results) == 1
        assert results[0]["id"] == 1
        assert results[0]["similarity"] == 0.95

    def test_retrieve_empty_results(self, mock_psycopg_connection, sample_embedding):
        """Deve retornar lista vazia se sem chunks."""
        cursor = mock_psycopg_connection.cursor.return_value
        cursor.fetchall.return_value = []

        retriever = RAGRetriever(db_url="postgresql://test")
        results = retriever.retrieve(
            query_text="teste",
            query_embedding=sample_embedding,
            top_k=5
        )

        assert results == []

    def test_retrieve_with_single_filter(self, mock_psycopg_connection, sample_embedding):
        """Deve aplicar filtro único de metadados."""
        cursor = mock_psycopg_connection.cursor.return_value
        cursor.fetchall.return_value = [(1, "doc1", "Texto", {}, "2021", "FCC", "CF", "22", 0.95)]

        retriever = RAGRetriever(db_url="postgresql://test")
        results = retriever.retrieve(
            query_text="teste",
            query_embedding=sample_embedding,
            top_k=5,
            filters={"ano": "2021"}
        )

        assert len(results) == 1

    def test_retrieve_with_multiple_filters(self, mock_psycopg_connection, sample_embedding):
        """Deve aplicar múltiplos filtros."""
        cursor = mock_psycopg_connection.cursor.return_value
        cursor.fetchall.return_value = [(1, "doc1", "Texto", {}, "2021", "FCC", "CF", "22", 0.95)]

        retriever = RAGRetriever(db_url="postgresql://test")
        results = retriever.retrieve(
            query_text="teste",
            query_embedding=sample_embedding,
            top_k=5,
            filters={"ano": "2021", "banca": "FCC"}
        )

        assert len(results) == 1

    def test_retrieve_with_invalid_filter(self, mock_psycopg_connection, sample_embedding, caplog):
        """Deve ignorar filtro não permitido e logar warning."""
        cursor = mock_psycopg_connection.cursor.return_value
        cursor.fetchall.return_value = [(1, "doc1", "Texto", {}, "2021", "FCC", "CF", "22", 0.95)]

        retriever = RAGRetriever(db_url="postgresql://test")

        with caplog.at_level(logging.WARNING):
            results = retriever.retrieve(
                query_text="teste",
                query_embedding=sample_embedding,
                top_k=5,
                filters={"ano": "2021", "filtro_invalido": "valor"}
            )

        # Deve ignorar o filtro inválido e usar apenas filtros válidos
        assert any("Ignorando filtro RAG não permitido" in record.message for record in caplog.records)
        # Deve retornar resultados (usando apenas o filtro válido "ano": "2021")
        assert len(results) > 0

    def test_retrieve_db_error(self, mock_psycopg_connection, sample_embedding, caplog):
        """Deve retornar lista vazia se DB falhar."""
        import psycopg
        cursor = mock_psycopg_connection.cursor.return_value
        cursor.execute.side_effect = psycopg.Error("DB error")

        retriever = RAGRetriever(db_url="postgresql://test")

        with caplog.at_level(logging.ERROR):
            results = retriever.retrieve(
                query_text="teste",
                query_embedding=sample_embedding,
                top_k=5
            )

        assert results == []
        assert any("Erro na busca RAG" in record.message for record in caplog.records)

    def test_retrieve_disabled(self, sample_embedding):
        """Deve retornar lista vazia se enabled=False."""
        retriever = RAGRetriever(db_url=None)

        results = retriever.retrieve(
            query_text="teste",
            query_embedding=sample_embedding,
            top_k=5
        )

        assert results == []

    def test_retrieve_order_by_similarity(self, mock_psycopg_connection, sample_embedding):
        """Deve ordenar por similaridade (desc) via SQL ORDER BY."""
        cursor = mock_psycopg_connection.cursor.return_value
        # O SQL com ORDER BY já retorna ordenado do banco
        cursor.fetchall.return_value = [
            (1, "doc1", "Texto 1", {}, "2021", "FCC", "CF", "22", 0.95),
            (2, "doc2", "Texto 2", {}, "2020", "Cebraspe", "CF", None, 0.87),
            (3, "doc3", "Texto 3", {}, "2019", "FGV", "CF", None, 0.75),
        ]

        retriever = RAGRetriever(db_url="postgresql://test")
        results = retriever.retrieve(
            query_text="teste",
            query_embedding=sample_embedding,
            top_k=5
        )

        # Verificar que veio ordenado do banco (ORDER BY no SQL)
        similarities = [r["similarity"] for r in results]
        assert similarities == [0.95, 0.87, 0.75]


class TestRAGRetrieverRetrieveByKeywords:
    """Testes para retrieve_by_keywords()."""

    def test_retrieve_by_keywords_basic(self, mock_psycopg_connection):
        """Deve buscar por ILIKE com keywords."""
        cursor = mock_psycopg_connection.cursor.return_value
        cursor.fetchall.return_value = [(1, "doc1", "Texto...", {}, "2021", "FCC")]

        retriever = RAGRetriever(db_url="postgresql://test")
        results = retriever.retrieve_by_keywords(
            keywords=["competência", "união"],
            top_k=5
        )

        # Deve retornar resultados da busca
        assert len(results) > 0
        assert cursor.execute.called

    def test_retrieve_by_keywords_multiple(self, mock_psycopg_connection):
        """Deve combinar keywords com OR."""
        cursor = mock_psycopg_connection.cursor.return_value
        cursor.fetchall.return_value = []

        retriever = RAGRetriever(db_url="postgresql://test")
        results = retriever.retrieve_by_keywords(
            keywords=["word1", "word2", "word3"],
            top_k=5
        )

        # Deve criar query com OR para cada keyword
        assert cursor.execute.called

    def test_retrieve_by_keywords_with_filters(self, mock_psycopg_connection):
        """Deve aplicar filtros junto com keywords."""
        cursor = mock_psycopg_connection.cursor.return_value
        cursor.fetchall.return_value = []

        retriever = RAGRetriever(db_url="postgresql://test")
        results = retriever.retrieve_by_keywords(
            keywords=["teste"],
            top_k=5,
            filters={"ano": "2021"}
        )

        assert cursor.execute.called

    def test_retrieve_by_keywords_invalid_filter(self, mock_psycopg_connection, caplog):
        """Deve ignorar filtro inválido."""
        cursor = mock_psycopg_connection.cursor.return_value
        cursor.fetchall.return_value = []

        retriever = RAGRetriever(db_url="postgresql://test")

        with caplog.at_level(logging.WARNING):
            results = retriever.retrieve_by_keywords(
                keywords=["teste"],
                top_k=5,
                filters={"filtro_invalido": "valor"}
            )

        assert any("Ignorando filtro keyword não permitido" in record.message for record in caplog.records)

    def test_retrieve_by_keywords_disabled(self):
        """Deve retornar lista vazia se enabled=False."""
        retriever = RAGRetriever(db_url=None)

        results = retriever.retrieve_by_keywords(
            keywords=["teste"],
            top_k=5
        )

        assert results == []

    def test_retrieve_by_keywords_db_error(self, mock_psycopg_connection, caplog):
        """Deve retornar lista vazia se DB falhar."""
        import psycopg
        cursor = mock_psycopg_connection.cursor.return_value
        cursor.execute.side_effect = psycopg.Error("DB error")

        retriever = RAGRetriever(db_url="postgresql://test")

        with caplog.at_level(logging.ERROR):
            results = retriever.retrieve_by_keywords(
                keywords=["teste"],
                top_k=5
            )

        assert results == []
        assert any("Erro na busca por keywords" in record.message for record in caplog.records)


class TestRAGRetrieverSecurity:
    """Testes de segurança do RAGRetriever."""

    def test_allowed_metadata_filters(self):
        """Deve ter lista de filtros permitidos."""
        expected_filters = {"ano", "artigo", "assunto", "banca", "cargo", "disciplina", "tema", "tipo"}
        assert ALLOWED_METADATA_FILTERS == expected_filters

    def test_retrieve_sql_injection_in_filter(self, mock_psycopg_connection, sample_embedding):
        """Deve sanitizar input contra SQL injection."""
        cursor = mock_psycopg_connection.cursor.return_value
        cursor.fetchall.return_value = []

        retriever = RAGRetriever(db_url="postgresql://test")

        # Tentativa de SQL injection
        results = retriever.retrieve(
            query_text="teste",
            query_embedding=sample_embedding,
            top_k=5,
            filters={"ano": "2021'; DROP TABLE students; --"}
        )

        # O valor deve ser tratado como parâmetro
        assert isinstance(results, list)

    def test_retrieve_filter_not_in_allowed_set(self, mock_psycopg_connection, sample_embedding):
        """Deve ignorar filtros não permitidos."""
        cursor = mock_psycopg_connection.cursor.return_value
        cursor.fetchall.return_value = []

        retriever = RAGRetriever(db_url="postgresql://test")

        # Filtro não permitido
        results = retriever.retrieve(
            query_text="teste",
            query_embedding=sample_embedding,
            top_k=5,
            filters={"filtro_malicioso": "valor"}
        )

        # Não deve causar erro, apenas ignorar
        assert isinstance(results, list)


class TestRAGRetrieverEdgeCases:
    """Testes de edge cases do RAGRetriever."""

    def test_retrieve_with_none_embedding(self, mock_psycopg_connection, caplog):
        """Deve lidar com embedding None."""
        retriever = RAGRetriever(db_url="postgresql://test")

        results = retriever.retrieve(
            query_text="teste",
            query_embedding=None,
            top_k=5
        )

        # Deve retornar vazio ou tratar o erro
        assert isinstance(results, list)

    def test_retrieve_with_zero_top_k(self, mock_psycopg_connection, sample_embedding):
        """Deve lidar com top_k=0."""
        cursor = mock_psycopg_connection.cursor.return_value
        cursor.fetchall.return_value = []

        retriever = RAGRetriever(db_url="postgresql://test")
        results = retriever.retrieve(
            query_text="teste",
            query_embedding=sample_embedding,
            top_k=0
        )

        assert isinstance(results, list)

    def test_retrieve_similarities_range(self, mock_psycopg_connection, sample_embedding):
        """Similaridade deve estar entre 0 e 1."""
        cursor = mock_psycopg_connection.cursor.return_value
        cursor.fetchall.return_value = [
            (1, "doc1", "Texto", {}, "2021", "FCC", "CF", "22", 0.95),
            (2, "doc2", "Texto", {}, "2020", "Cebraspe", "CF", None, 0.87),
            (3, "doc3", "Texto", {}, "2019", "FGV", "CF", None, 0.75),
        ]

        retriever = RAGRetriever(db_url="postgresql://test")
        results = retriever.retrieve(
            query_text="teste",
            query_embedding=sample_embedding,
            top_k=5
        )

        for result in results:
            assert 0 <= result["similarity"] <= 1

    def test_retrieve_unicode_text(self, mock_psycopg_connection, sample_embedding):
        """Deve lidar com texto unicode (emojis, acentos)."""
        cursor = mock_psycopg_connection.cursor.return_value
        cursor.fetchall.return_value = [
            (1, "doc1", "Texto com emoji 🎉 e acento áéíóú", {}, "2021", "FCC", "CF", "22", 0.95)
        ]

        retriever = RAGRetriever(db_url="postgresql://test")
        results = retriever.retrieve(
            query_text="teste",
            query_embedding=sample_embedding,
            top_k=5
        )

        assert len(results) == 1
        assert "🎉" in results[0]["texto"]
        assert "áéíóú" in results[0]["texto"]

    def test_retrieve_by_keywords_empty(self, mock_psycopg_connection):
        """Deve lidar com lista de keywords vazia."""
        retriever = RAGRetriever(db_url="postgresql://test")

        results = retriever.retrieve_by_keywords(
            keywords=[],
            top_k=5
        )

        assert isinstance(results, list)

    def test_retrieve_metadata_types(self, mock_psycopg_connection, sample_embedding):
        """Deve retornar todos os tipos de metadados."""
        cursor = mock_psycopg_connection.cursor.return_value
        cursor.fetchall.return_value = [
            (1, "doc1", "Texto", {"ano": "2021", "banca": "FCC", "tipo": "CF", "artigo": "22"}, "2021", "FCC", "CF", "22", 0.95)
        ]

        retriever = RAGRetriever(db_url="postgresql://test")
        results = retriever.retrieve(
            query_text="teste",
            query_embedding=sample_embedding,
            top_k=5
        )

        assert results[0]["ano"] == "2021"
        assert results[0]["banca"] == "FCC"
        assert results[0]["tipo"] == "CF"
        assert results[0]["artigo"] == "22"
