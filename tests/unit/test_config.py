"""Testes unitários para config.py."""

import os
from unittest.mock import patch, Mock
import pytest

from oraculo_bot import config


class TestRequireEnv:
    """Testes para _require_env()."""

    def test_require_env_with_valid_value(self, monkeypatch):
        """Deve retornar o valor quando env var existe."""
        monkeypatch.setenv("TEST_VAR", "test_value")
        result = config._require_env("TEST_VAR")
        assert result == "test_value"

    def test_require_env_with_missing_value(self, monkeypatch):
        """Deve levantar ValueError quando env var não existe."""
        monkeypatch.delenv("TEST_VAR", raising=False)
        with pytest.raises(ValueError, match="Variável de ambiente 'TEST_VAR' não definida"):
            config._require_env("TEST_VAR")

    def test_require_env_with_empty_string(self, monkeypatch):
        """Deve levantar ValueError quando env var é string vazia."""
        monkeypatch.setenv("TEST_VAR", "")
        with pytest.raises(ValueError, match="Variável de ambiente 'TEST_VAR' não definida"):
            config._require_env("TEST_VAR")


class TestConfigIntegration:
    """Testes de integração para valores de configuração do .env real.

    NOTA: Estes testes dependem de variáveis de ambiente reais do .env.
    São testes de integração, não unitários puros.
    """

    def test_discord_bot_token_is_set(self):
        """Deve ter DISCORD_BOT_TOKEN configurado (do .env)."""
        assert config.DISCORD_BOT_TOKEN is not None
        assert isinstance(config.DISCORD_BOT_TOKEN, str)

    def test_deepseek_api_key_is_set(self):
        """Deve ter DEEPSEEK_API_KEY configurado (do .env)."""
        assert config.DEEPSEEK_API_KEY is not None
        assert isinstance(config.DEEPSEEK_API_KEY, str)

    def test_model_id_has_default(self):
        """Deve ter default para MODEL_ID."""
        assert config.MODEL_ID is not None
        assert isinstance(config.MODEL_ID, str)

    def test_history_runs_has_default(self):
        """Deve ter default para HISTORY_RUNS."""
        assert config.HISTORY_RUNS is not None
        assert isinstance(config.HISTORY_RUNS, int)

    def test_max_message_length_is_set(self):
        """Deve ter MAX_MESSAGE_LENGTH configurado."""
        assert config.MAX_MESSAGE_LENGTH == 1500

    def test_thread_name_prefix_is_set(self):
        """Deve ter THREAD_NAME_PREFIX configurado."""
        assert config.THREAD_NAME_PREFIX == "💬"

    def test_error_message_is_set(self):
        """Deve ter ERROR_MESSAGE configurado."""
        assert config.ERROR_MESSAGE is not None
        assert isinstance(config.ERROR_MESSAGE, str)


class TestOptionalConfigValues:
    """Testes para valores opcionais."""

    def test_supabase_db_url_is_optional(self):
        """SUPABASE_DB_URL pode ser None ou string."""
        assert config.SUPABASE_DB_URL is None or isinstance(config.SUPABASE_DB_URL, str)

    def test_openai_api_key_is_optional(self):
        """OPENAI_API_KEY pode ser None ou string."""
        assert config.OPENAI_API_KEY is None or isinstance(config.OPENAI_API_KEY, str)

    def test_gemini_api_key_is_optional(self):
        """GEMINI_API_KEY pode ser None ou string."""
        assert config.GEMINI_API_KEY is None or isinstance(config.GEMINI_API_KEY, str)


class TestDiscordIDs:
    """Testes para IDs do Discord."""

    def test_target_guild_id_is_int(self):
        """TARGET_GUILD_ID deve ser int."""
        assert isinstance(config.TARGET_GUILD_ID, int)

    def test_target_channel_id_is_int(self):
        """TARGET_CHANNEL_ID deve ser int."""
        assert isinstance(config.TARGET_CHANNEL_ID, int)


class TestSystemInstructions:
    """Testes para SYSTEM_INSTRUCTIONS em agent.py."""

    def test_system_instructions_defined(self):
        """SYSTEM_INSTRUCTIONS deve estar definida."""
        from oraculo_bot import agent
        assert hasattr(agent, "SYSTEM_INSTRUCTIONS")
        assert isinstance(agent.SYSTEM_INSTRUCTIONS, list)
        assert len(agent.SYSTEM_INSTRUCTIONS) > 0

    def test_system_instructions_content(self):
        """SYSTEM_INSTRUCTIONS deve ter conteúdo relevante."""
        from oraculo_bot import agent
        all_text = " ".join(agent.SYSTEM_INSTRUCTIONS)
        assert "Oráculo" in all_text
        assert "concursos" in all_text.lower()
