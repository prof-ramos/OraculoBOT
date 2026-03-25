"""Testes unitários para agent.py."""

from unittest.mock import Mock, MagicMock, patch, call
import pytest

from oraculo_bot import agent
from oraculo_bot.models import DiscordSession


class TestCreateAgent:
    """Testes para create_agent()."""

    def test_create_agent_returns_agent_instance(self, mocker):
        """Deve retornar instância de Agent."""
        mock_deepseek = mocker.patch("oraculo_bot.agent.DeepSeek")
        mock_agent_class = mocker.patch("oraculo_bot.agent.Agent")

        mock_agent_instance = Mock()
        mock_agent_class.return_value = mock_agent_instance

        result = agent.create_agent()

        assert result is mock_agent_instance
        mock_agent_class.assert_called_once()

    def test_create_agent_uses_config_values(self, mocker, mock_env_vars):
        """Deve usar valores do config."""
        mock_deepseek = mocker.patch("oraculo_bot.agent.DeepSeek")
        mock_agent_class = mocker.patch("oraculo_bot.agent.Agent")

        agent.create_agent()

        # Verificar chamadas
        mock_agent_class.assert_called_once()
        call_kwargs = mock_agent_class.call_args[1]

        assert call_kwargs["name"] == "Oráculo"
        assert call_kwargs["markdown"] is True
        assert call_kwargs["add_history_to_context"] is True
        assert call_kwargs["num_history_runs"] == 5
        assert call_kwargs["add_datetime_to_context"] is True

    def test_create_agent_includes_system_instructions(self, mocker):
        """Deve incluir SYSTEM_INSTRUCTIONS."""
        mock_agent_class = mocker.patch("oraculo_bot.agent.Agent")
        mocker.patch("oraculo_bot.agent.DeepSeek")

        agent.create_agent()

        call_kwargs = mock_agent_class.call_args[1]
        assert "instructions" in call_kwargs
        assert isinstance(call_kwargs["instructions"], list)
        assert len(call_kwargs["instructions"]) > 0


class TestInitializeSession:
    """Testes para initialize_session()."""

    def test_initialize_session_creates_via_dao(self, mocker):
        """Deve criar sessão via SessionDAO."""
        mock_dao = mocker.patch("oraculo_bot.agent._session_dao")
        mock_session = DiscordSession(
            thread_id="thread123",
            user_id="user123",
            mode="estudo"
        )
        mock_dao.get_or_create_session.return_value = mock_session

        result = agent.initialize_session("thread123", "user123", "professor")

        assert result.thread_id == "thread123"
        mock_dao.get_or_create_session.assert_called_once_with(
            "thread123",
            "user123",
            "professor"
        )

    def test_initialize_session_default_mode(self, mocker):
        """Deve usar modo 'estudo' como default."""
        mock_dao = mocker.patch("oraculo_bot.agent._session_dao")
        mock_session = DiscordSession(
            thread_id="thread123",
            user_id="user123",
            mode="estudo"
        )
        mock_dao.get_or_create_session.return_value = mock_session

        result = agent.initialize_session("thread123", "user123")

        mock_dao.get_or_create_session.assert_called_once_with(
            "thread123",
            "user123",
            "estudo"
        )


class TestSaveSessionHistory:
    """Testes para save_session_history()."""

    def test_save_session_history_calls_dao(self, mocker):
        """Deve chamar update_session_data do DAO."""
        mock_dao = mocker.patch("oraculo_bot.agent._session_dao")
        mock_session = DiscordSession(
            thread_id="thread123",
            user_id="user123",
            mode="estudo"
        )
        mock_dao.update_session_data.return_value = mock_session

        messages = [
            {"role": "user", "content": "Olá"},
            {"role": "assistant", "content": "Oi!"}
        ]

        agent.save_session_history("thread123", messages)

        mock_dao.update_session_data.assert_called_once_with(
            "thread123",
            {"history": messages}
        )

    def test_save_session_history_with_empty_messages(self, mocker):
        """Deve lidar com lista vazia de mensagens."""
        mock_dao = mocker.patch("oraculo_bot.agent._session_dao")
        mock_session = DiscordSession(
            thread_id="thread123",
            user_id="user123",
            mode="estudo"
        )
        mock_dao.update_session_data.return_value = mock_session

        agent.save_session_history("thread123", [])

        mock_dao.update_session_data.assert_called_once_with(
            "thread123",
            {"history": []}
        )


class TestGetSessionHistory:
    """Testes para get_session_history()."""

    def test_get_session_history_from_dao(self, mocker):
        """Deve buscar histórico do DAO."""
        mock_dao = mocker.patch("oraculo_bot.agent._session_dao")
        mock_session = DiscordSession(
            thread_id="thread123",
            user_id="user123",
            mode="estudo",
            session_data={
                "history": [
                    {"role": "user", "content": "Pergunta"},
                    {"role": "assistant", "content": "Resposta"}
                ]
            }
        )
        mock_dao.get_session.return_value = mock_session

        result = agent.get_session_history("thread123")

        assert result == [
            {"role": "user", "content": "Pergunta"},
            {"role": "assistant", "content": "Resposta"}
        ]

    def test_get_session_history_returns_empty_list_if_no_session(self, mocker):
        """Deve retornar lista vazia se sessão não existe."""
        mock_dao = mocker.patch("oraculo_bot.agent._session_dao")
        mock_dao.get_session.return_value = None

        result = agent.get_session_history("thread999")

        assert result == []

    def test_get_session_history_returns_empty_list_if_no_history(self, mocker):
        """Deve retornar lista vazia se sem histórico."""
        mock_dao = mocker.patch("oraculo_bot.agent._session_dao")
        mock_session = DiscordSession(
            thread_id="thread123",
            user_id="user123",
            mode="estudo",
            session_data={}
        )
        mock_dao.get_session.return_value = mock_session

        result = agent.get_session_history("thread123")

        assert result == []

    def test_get_session_history_returns_empty_list_if_no_session_data(self, mocker):
        """Deve retornar lista vazia se session_data não tem histórico."""
        mock_dao = mocker.patch("oraculo_bot.agent._session_dao")
        mock_session = DiscordSession(
            thread_id="thread123",
            user_id="user123",
            mode="estudo",
            session_data={}  # Vazio, não None
        )
        mock_dao.get_session.return_value = mock_session

        result = agent.get_session_history("thread123")

        assert result == []


class TestCleanupOldSessions:
    """Testes para cleanup_old_sessions()."""

    def test_cleanup_old_sessions_delegates_to_dao(self, mocker):
        """Deve delegar para SessionDAO."""
        mock_dao = mocker.patch("oraculo_bot.agent._session_dao")
        mock_dao.cleanup_old_sessions.return_value = 10

        result = agent.cleanup_old_sessions(days=30)

        assert result == 10
        mock_dao.cleanup_old_sessions.assert_called_once_with(30)

    def test_cleanup_old_sessions_default_days(self, mocker):
        """Deve usar 30 dias como default."""
        mock_dao = mocker.patch("oraculo_bot.agent._session_dao")
        mock_dao.cleanup_old_sessions.return_value = 5

        result = agent.cleanup_old_sessions()

        mock_dao.cleanup_old_sessions.assert_called_once_with(30)
        assert result == 5


class TestEnrichWithRAG:
    """Testes para enrich_with_rag()."""

    def test_enrich_with_rag_success(self, mocker):
        """Deve enriquecer query com contexto RAG."""
        mock_retrieve = mocker.patch(
            "oraculo_bot.rag.retrieve_relevant_legislation",
            return_value="Art. 22. Compete privativamente à União..."
        )

        result = agent.enrich_with_rag("competência união trabalho", top_k=3)

        assert "[CONTEXTO LEGISLATIVO RELEVANTE]" in result
        assert "Art. 22" in result
        mock_retrieve.assert_called_once_with(
            query_text="competência união trabalho",
            top_k=3
        )

    def test_enrich_with_rag_no_results(self, mocker):
        """Deve retornar string vazia se RAG não retorna nada."""
        mocker.patch(
            "oraculo_bot.rag.retrieve_relevant_legislation",
            return_value=""
        )

        result = agent.enrich_with_rag("query sem resultados", top_k=3)

        assert result == ""

    def test_enrich_with_rag_error_fallback(self, mocker, caplog):
        """Deve retornar string vazia se RAG falhar."""
        mocker.patch(
            "oraculo_bot.rag.retrieve_relevant_legislation",
            side_effect=Exception("RAG failed")
        )

        result = agent.enrich_with_rag("query", top_k=3)

        assert result == ""
        assert any("RAG fallback" in record.message for record in caplog.records)

    def test_enrich_with_rag_default_top_k(self, mocker):
        """Deve usar top_k=3 como default."""
        mock_retrieve = mocker.patch(
            "oraculo_bot.rag.retrieve_relevant_legislation",
            return_value="Contexto RAG"
        )

        agent.enrich_with_rag("query")

        mock_retrieve.assert_called_once_with(
            query_text="query",
            top_k=3
        )

    def test_enrich_with_rag_formatting(self, mocker):
        """Deve formatar contexto corretamente."""
        mocker.patch(
            "oraculo_bot.rag.retrieve_relevant_legislation",
            return_value="Legislação relevante aqui"
        )

        result = agent.enrich_with_rag("query")

        # Verificar formato
        assert result.startswith("\n\n[CONTEXTO LEGISLATIVO RELEVANT")
        assert result.endswith("Legislação relevante aqui\n")

    def test_enrich_with_rag_with_multiple_chunks(self, mocker):
        """Deve formatar múltiplos chunks."""
        rag_content = """
[Fonte 1 (ano: 2021, banca: FCC)]
Texto do chunk 1

[Fonte 2 (ano: 2020, banca: Cebraspe)]
Texto do chunk 2
        """.strip()

        mocker.patch(
            "oraculo_bot.rag.retrieve_relevant_legislation",
            return_value=rag_content
        )

        result = agent.enrich_with_rag("query")

        assert "[CONTEXTO LEGISLATIVO RELEVANTE]" in result
        assert "Fonte 1" in result
        assert "Fonte 2" in result


class TestSystemInstructions:
    """Testes para SYSTEM_INSTRUCTIONS."""

    def test_system_instructions_is_list(self):
        """Deve ser uma lista."""
        assert isinstance(agent.SYSTEM_INSTRUCTIONS, list)

    def test_system_instructions_not_empty(self):
        """Deve ter instruções definidas."""
        assert len(agent.SYSTEM_INSTRUCTIONS) > 0

    def test_system_instructions_contains_identity(self):
        """Deve conter identidade do Oráculo."""
        all_text = " ".join(agent.SYSTEM_INSTRUCTIONS)
        assert "Oráculo" in all_text
        assert "concursos" in all_text.lower()

    def test_system_instructions_contains_modes(self):
        """Deve conter modos de operação."""
        all_text = " ".join(agent.SYSTEM_INSTRUCTIONS)
        assert "ESTUDO" in all_text
        assert "PROFESSOR" in all_text
        assert "SIMULADO" in all_text
        assert "CASUAL" in all_text

    def test_system_instructions_contains_restrictions(self):
        """Deve conter restrições."""
        all_text = " ".join(agent.SYSTEM_INSTRUCTIONS)
        assert "Não invente" in all_text or "nunca invente" in all_text.lower()

    def test_system_instructions_contains_formatting(self):
        """Deve conter instruções de formatação Discord."""
        all_text = " ".join(agent.SYSTEM_INSTRUCTIONS)
        assert "Markdown" in all_text
        assert "Discord" in all_text


class TestAgentIntegration:
    """Testes de integração do agent."""

    def test_initialize_and_save_history_flow(self, mocker):
        """Deve fluir de criação → salvar histórico."""
        mock_dao = mocker.patch("oraculo_bot.agent._session_dao")

        # Criar sessão
        mock_session = DiscordSession(
            thread_id="thread123",
            user_id="user123",
            mode="estudo"
        )
        mock_dao.get_or_create_session.return_value = mock_session
        mock_dao.update_session_data.return_value = mock_session

        # Executar fluxo
        session = agent.initialize_session("thread123", "user123")
        messages = [{"role": "user", "content": "Test"}]
        agent.save_session_history("thread123", messages)

        # Verificar
        mock_dao.get_or_create_session.assert_called_once()
        mock_dao.update_session_data.assert_called_once()

    def test_get_history_after_save(self, mocker):
        """Deve recuperar histórico salvo."""
        mock_dao = mocker.patch("oraculo_bot.agent._session_dao")

        messages = [
            {"role": "user", "content": "P1"},
            {"role": "assistant", "content": "R1"},
            {"role": "user", "content": "P2"},
        ]

        mock_session = DiscordSession(
            thread_id="thread123",
            user_id="user123",
            mode="estudo",
            session_data={"history": messages}
        )

        mock_dao.update_session_data.return_value = mock_session
        mock_dao.get_session.return_value = mock_session

        # Salvar
        agent.save_session_history("thread123", messages)

        # Recuperar
        retrieved = agent.get_session_history("thread123")

        assert retrieved == messages

    def test_cleanup_flow(self, mocker):
        """Deve executar cleanup corretamente."""
        mock_dao = mocker.patch("oraculo_bot.agent._session_dao")
        mock_dao.cleanup_old_sessions.return_value = 15

        count = agent.cleanup_old_sessions(days=60)

        assert count == 15
        mock_dao.cleanup_old_sessions.assert_called_once_with(60)


class TestAgentEdgeCases:
    """Testes de edge cases para agent.py."""

    def test_enrich_with_rag_none_return(self, mocker):
        """Deve lidar com None de retrieve_relevant_legislation."""
        mocker.patch(
            "oraculo_bot.rag.retrieve_relevant_legislation",
            return_value=None
        )

        result = agent.enrich_with_rag("query")

        assert result == ""

    def test_save_history_with_complex_messages(self, mocker):
        """Deve salvar mensagens com estrutura complexa."""
        mock_dao = mocker.patch("oraculo_bot.agent._session_dao")
        mock_session = DiscordSession(
            thread_id="thread123",
            user_id="user123",
            mode="estudo"
        )
        mock_dao.update_session_data.return_value = mock_session

        complex_messages = [
            {
                "role": "user",
                "content": "Texto",
                "metadata": {"images": ["url1", "url2"]},
                "timestamp": "2024-01-01T00:00:00Z"
            },
            {
                "role": "assistant",
                "content": "Resposta",
                "tools_used": ["search", "calculate"]
            }
        ]

        agent.save_session_history("thread123", complex_messages)

        mock_dao.update_session_data.assert_called_once_with(
            "thread123",
            {"history": complex_messages}
        )

    def test_get_history_with_malformed_session_data(self, mocker):
        """Deve lidar com session_data malformado."""
        mock_dao = mocker.patch("oraculo_bot.agent._session_dao")
        mock_session = DiscordSession(
            thread_id="thread123",
            user_id="user123",
            mode="estudo",
            session_data={"history": "not_a_list"}
        )
        mock_dao.get_session.return_value = mock_session

        result = agent.get_session_history("thread123")

        # Deve retornar o valor como está (não valida tipo)
        assert result == "not_a_list"

    def test_initialize_with_all_modes(self, mocker):
        """Deve aceitar todos os modos válidos."""
        mock_dao = mocker.patch("oraculo_bot.agent._session_dao")

        modes = ["estudo", "professor", "simulado", "casual"]

        for mode in modes:
            # Criar sessão com o modo correto para cada iteração
            mock_session = DiscordSession(
                thread_id="thread1",
                user_id="user1",
                mode=mode  # Usar o modo atual
            )
            mock_dao.get_or_create_session.return_value = mock_session

            result = agent.initialize_session("thread1", "user1", mode)

            # Verificar que o modo correto foi retornado
            assert result.mode == mode
            # Verificar que DAO foi chamado com o modo correto
            mock_dao.get_or_create_session.assert_called_with("thread1", "user1", mode)
