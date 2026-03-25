"""Fixtures compartilhadas para testes do OraculoBOT."""

import os
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone

import pytest


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Configura variáveis de ambiente obrigatórias para testes."""
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "test_token_12345")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test_deepseek_key")
    monkeypatch.setenv("SUPABASE_DB_URL", "postgresql://test_user:test_pass@localhost:5432/test_db")
    return {
        "DISCORD_BOT_TOKEN": "test_token_12345",
        "DEEPSEEK_API_KEY": "test_deepseek_key",
        "SUPABASE_DB_URL": "postgresql://test_user:test_pass@localhost:5432/test_db",
    }


@pytest.fixture
def mock_env_vars_optional(monkeypatch):
    """Configura env vars opcionais."""
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")
    monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_key")
    monkeypatch.setenv("MODEL_ID", "deepseek-chat")
    monkeypatch.setenv("HISTORY_RUNS", "5")
    return {
        "OPENAI_API_KEY": "test_openai_key",
        "GEMINI_API_KEY": "test_gemini_key",
        "MODEL_ID": "deepseek-chat",
        "HISTORY_RUNS": "5",
    }


@pytest.fixture
def mock_discord_message():
    """Mock de Discord Message."""
    msg = Mock()
    msg.author.name = "TestUser"
    msg.author.id = 123456789
    msg.content = "Qual é a competência da União?"
    msg.attachments = []
    msg.guild.id = 1283924742851661844
    msg.channel.id = 1486301006659715143
    msg.channel.name = "geral"
    msg.jump_url = "https://discord.com/channels/1283924742851661844/1486301006659715143/123"
    msg.channel.type = 0  # TextChannel
    return msg


@pytest.fixture
def mock_agent_response():
    """Mock de Agno RunOutput."""
    response = Mock()
    response.status = "success"
    response.content = "Esta é uma resposta de teste do agente."
    response.messages = [
        {"role": "user", "content": "Qual é a competência da União?"},
        {"role": "assistant", "content": "Esta é uma resposta de teste do agente."},
    ]
    response.is_paused = False
    response.tools_requiring_confirmation = []
    response.reasoning_content = None
    return response


@pytest.fixture
def mock_paused_agent_response():
    """Mock de Agno RunOutput pausado (HITL)."""
    response = Mock()
    response.status = "paused"
    response.content = "Aguardando confirmação"
    response.messages = []
    response.is_paused = True
    response.tools_requiring_confirmation = [Mock(tool_name="test_tool")]
    response.reasoning_content = None
    return response


@pytest.fixture
def mock_error_agent_response():
    """Mock de Agno RunOutput com erro."""
    response = Mock()
    response.status = "error"
    response.content = "Erro interno"
    response.messages = []
    response.is_paused = False
    response.tools_requiring_confirmation = []
    return response


@pytest.fixture
def mock_sqlalchemy_session(mocker):
    """Mock de SQLAlchemy Session."""
    session = MagicMock()
    session.__enter__ = Mock(return_value=session)
    session.__exit__ = Mock(return_value=False)
    return session


@pytest.fixture
def mock_sqlalchemy_engine(mocker):
    """Mock de SQLAlchemy Engine."""
    engine = MagicMock()
    mocker.patch("oraculo_bot.db.create_engine", return_value=engine)
    return engine


@pytest.fixture
def mock_psycopg_connection(mocker):
    """Mock de conexão psycopg com cursor."""
    conn = MagicMock()
    cursor = MagicMock()

    # Configurar o cursor como context manager
    cursor.__enter__ = Mock(return_value=cursor)
    cursor.__exit__ = Mock(return_value=False)
    conn.cursor.return_value = cursor

    mocker.patch("psycopg.connect", return_value=conn)

    # Retornar ambos para facilitar acesso nos testes
    return conn


@pytest.fixture
def sample_embedding():
    """Embedding de exemplo para testes."""
    return [0.1] * 1536  # Dimensão padrão OpenAI


@pytest.fixture
def sample_rag_chunks():
    """Chunks RAG de exemplo."""
    return [
        {
            "id": 1,
            "documento_id": "doc_1",
            "texto": "Art. 22. Compete privativamente à União legislar sobre direito do trabalho.",
            "metadados": {"ano": "2021", "banca": "FCC", "tipo": "CF", "artigo": "22"},
            "ano": "2021",
            "banca": "FCC",
            "tipo": "CF",
            "artigo": "22",
            "similarity": 0.95,
        },
        {
            "id": 2,
            "documento_id": "doc_2",
            "texto": "A União, os Estados e o Distrito Federal poderão legislar concorrentemente.",
            "metadados": {"ano": "2020", "banca": "Cebraspe", "tipo": "CF"},
            "ano": "2020",
            "banca": "Cebraspe",
            "tipo": "CF",
            "artigo": None,
            "similarity": 0.87,
        },
    ]


@pytest.fixture
def sample_discord_session():
    """Sessão Discord de exemplo."""
    return {
        "thread_id": "thread_123",
        "user_id": "user_456",
        "mode": "estudo",
        "session_data": {"history": []},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


@pytest.fixture
def clean_env(monkeypatch):
    """Remove todas as env vars relacionadas ao projeto."""
    keys_to_remove = [
        "DISCORD_BOT_TOKEN",
        "DEEPSEEK_API_KEY",
        "OPENAI_API_KEY",
        "GEMINI_API_KEY",
        "SUPABASE_DB_URL",
        "TARGET_GUILD_ID",
        "TARGET_CHANNEL_ID",
        "MODEL_ID",
        "HISTORY_RUNS",
    ]
    for key in keys_to_remove:
        monkeypatch.delenv(key, raising=False)


# ── Discord Fixtures (P1) ────────────────────────────────────────

@pytest.fixture
def mock_discord_client(mocker):
    """Mock de Discord Client."""
    from unittest.mock import AsyncMock

    client = MagicMock()
    client.user = MagicMock()
    client.user.id = "bot123"
    client.user.name = "OraculoBOT"
    client.run = MagicMock()
    client.event = MagicMock()
    return client


@pytest.fixture
def mock_discord_text_channel(mocker):
    """Mock de Discord TextChannel."""
    from unittest.mock import AsyncMock
    from unittest.mock import MagicMock
    from oraculo_bot.config import TARGET_CHANNEL_ID
    import discord

    channel = MagicMock(spec=discord.TextChannel)
    channel.id = TARGET_CHANNEL_ID
    channel.name = "geral"
    channel.type = 0  # TextChannel
    channel.send = AsyncMock()
    channel.create_thread = AsyncMock()
    return channel


@pytest.fixture
def mock_discord_thread(mocker):
    """Mock de Discord Thread."""
    from unittest.mock import AsyncMock
    from unittest.mock import MagicMock
    from oraculo_bot.config import TARGET_CHANNEL_ID
    import discord

    thread = MagicMock(spec=discord.Thread)
    thread.id = "thread_123"
    thread.name = "💬 TestUser"
    thread.parent_id = TARGET_CHANNEL_ID
    thread.type = 11  # Thread
    thread.send = AsyncMock()
    thread.typing = AsyncMock()
    return thread


@pytest.fixture
def mock_discord_interaction(mocker):
    """Mock de Discord Interaction."""
    from unittest.mock import AsyncMock

    interaction = AsyncMock()
    interaction.response = MagicMock()
    interaction.response.edit_message = AsyncMock()
    interaction.user = MagicMock()
    interaction.user.id = 123456789
    return interaction


@pytest.fixture
def mock_discord_message_with_attachment(mocker):
    """Mock de Discord Message com attachment."""
    from unittest.mock import MagicMock

    msg = MagicMock()
    msg.author = MagicMock()
    msg.author.name = "TestUser"
    msg.author.id = 123456789
    msg.content = "Test message with attachment"

    # Mock attachment
    attachment = MagicMock()
    attachment.content_type = "image/png"
    attachment.url = "https://example.com/image.png"
    msg.attachments = [attachment]

    msg.guild = MagicMock()
    msg.guild.id = 1283924742851661844

    msg.channel = MagicMock()
    msg.channel.id = 1486301006659715143

    msg.jump_url = "https://discord.com/channels/123/456/789"
    return msg


@pytest.fixture
def mock_run_output():
    """Mock de Agno RunOutput básico."""
    response = MagicMock()
    response.status = "success"
    response.content = "Response text"
    response.messages = []
    response.is_paused = False
    response.tools_requiring_confirmation = []
    response.reasoning_content = None
    return response


@pytest.fixture
def mock_team_run_output():
    """Mock de Agno TeamRunOutput."""
    response = MagicMock()
    response.status = "success"
    response.content = "Team response"
    response.messages = []
    return response
