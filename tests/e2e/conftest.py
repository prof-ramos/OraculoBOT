"""Fixtures específicas para testes E2E do OraculoBOT."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, Mock

import discord
import pytest
import pytest_asyncio

from oraculo_bot.bot import OracleDiscordBot
from oraculo_bot.agent import create_agent
from oraculo_bot.views import ConfirmationView


# ── E2E Bot Fixture ─────────────────────────────────────────────

@pytest_asyncio.fixture
async def e2e_bot(mock_env_vars, mock_agent_response):
    """Bot configurado para testes E2E com agent mockado."""
    # Criar agent mockado
    agent = create_agent()
    agent.arun = AsyncMock(return_value=mock_agent_response)
    agent.acontinue_run = AsyncMock(return_value=mock_agent_response)

    # Criar bot
    bot = OracleDiscordBot(agent=agent)

    # Mock do client Discord com IDs inteiros
    bot.client._user = Mock()
    bot.client._user.id = 123456789012345678
    bot.client._user.name = "OraculoBOT"

    yield bot


# ── E2E Message Fixtures ─────────────────────────────────────────

@pytest.fixture
def e2e_message_text_only():
    """Mensagem Discord apenas com texto."""
    msg = MagicMock()
    msg.author = Mock()
    msg.author.name = "Estudante123"
    msg.author.id = 987654321
    msg.content = "Qual é o regime jurídico dos servidores públicos federais?"
    msg.attachments = []
    msg.guild = Mock()
    msg.guild.id = 1283924742851661844
    msg.channel = MagicMock(spec=discord.TextChannel)
    msg.channel.id = 1486301006659715143
    msg.jump_url = "https://discord.com/channels/1283924742851661844/1486301006659715143/999"
    msg.create_thread = AsyncMock()
    return msg


@pytest.fixture
def e2e_message_with_image():
    """Mensagem Discord com imagem anexa."""
    msg = MagicMock()
    msg.author = Mock()
    msg.author.name = "Estudante123"
    msg.author.id = 987654321
    msg.content = "Analisa essa questão de prova"
    msg.attachments = [Mock()]
    msg.attachments[0].content_type = "image/png"
    msg.attachments[0].url = "https://example.com/questao.png"
    msg.guild = Mock()
    msg.guild.id = 1283924742851661844
    msg.channel = MagicMock(spec=discord.TextChannel)
    msg.channel.id = 1486301006659715143
    msg.jump_url = "https://discord.com/channels/1283924742851661844/1486301006659715143/1000"
    msg.create_thread = AsyncMock()
    return msg


@pytest.fixture
def e2e_message_with_video():
    """Mensagem Discord com vídeo anexo."""
    msg = MagicMock()
    msg.author = Mock()
    msg.author.name = "Estudante456"
    msg.author.id = 123456789
    msg.content = "O que você acha dessa aula?"
    msg.attachments = [Mock()]
    msg.attachments[0].content_type = "video/mp4"
    msg.attachments[0].url = "https://example.com/aula.mp4"
    msg.guild = Mock()
    msg.guild.id = 1283924742851661844
    msg.channel = MagicMock(spec=discord.TextChannel)
    msg.channel.id = 1486301006659715143
    msg.jump_url = "https://discord.com/channels/1283924742851661844/1486301006659715143/1001"
    msg.create_thread = AsyncMock()
    return msg


@pytest.fixture
def e2e_message_with_audio():
    """Mensagem Discord com áudio anexo."""
    msg = MagicMock()
    msg.author = Mock()
    msg.author.name = "Estudante789"
    msg.author.id = 456789123
    msg.content = "Transcreve esse áudio"
    msg.attachments = [Mock()]
    msg.attachments[0].content_type = "audio/mpeg"
    msg.attachments[0].url = "https://example.com/podcast.mp3"
    msg.guild = Mock()
    msg.guild.id = 1283924742851661844
    msg.channel = MagicMock(spec=discord.TextChannel)
    msg.channel.id = 1486301006659715143
    msg.jump_url = "https://discord.com/channels/1283924742851661844/1486301006659715143/1002"
    msg.create_thread = AsyncMock()
    return msg


@pytest.fixture
def e2e_message_with_file():
    """Mensagem Discord com arquivo anexo (PDF)."""
    msg = MagicMock()
    msg.author = Mock()
    msg.author.name = "Estudante999"
    msg.author.id = 789123456
    msg.content = "Resume esse edital pra mim"
    msg.attachments = [Mock()]
    msg.attachments[0].content_type = "application/pdf"
    msg.attachments[0].url = "https://example.com/edital.pdf"
    msg.guild = Mock()
    msg.guild.id = 1283924742851661844
    msg.channel = MagicMock(spec=discord.TextChannel)
    msg.channel.id = 1486301006659715143
    msg.jump_url = "https://discord.com/channels/1283924742851661844/1486301006659715143/1003"
    msg.create_thread = AsyncMock()
    return msg


@pytest.fixture
def e2e_message_in_thread():
    """Mensagem enviada dentro de uma thread existente."""
    msg = MagicMock()
    msg.author = Mock()
    msg.author.name = "Estudante123"
    msg.author.id = 987654321
    msg.content = "Pode explicar melhor?"
    msg.attachments = []
    msg.guild = Mock()
    msg.guild.id = 1283924742851661844
    msg.channel = MagicMock(spec=discord.Thread)
    msg.channel.id = 1004
    msg.channel.parent_id = 1486301006659715143
    msg.jump_url = "https://discord.com/channels/1283924742851661844/1486301006659715143/1004"
    return msg


# ── E2E Thread/Channel Fixtures ───────────────────────────────────

@pytest.fixture
def e2e_thread():
    """Thread Discord mockada."""

    class TypingContextManager:
        async def __aenter__(self):
            return None
        async def __aexit__(self, *args):
            pass

    thread = MagicMock()  # Removido spec=discord.Thread para evitar conflito
    thread.id = 999123
    thread.name = "💬 Estudante123"
    thread.parent_id = 1486301006659715143
    thread.send = AsyncMock()
    thread.typing = Mock(return_value=TypingContextManager())
    return thread


@pytest.fixture
def e2e_text_channel():
    """Canal de texto Discord mockado."""
    channel = MagicMock(spec=discord.TextChannel)
    channel.id = 1486301006659715143
    channel.name = "geral"
    channel.send = AsyncMock()
    channel.create_thread = AsyncMock(return_value=MagicMock(spec=discord.Thread, id=999123))
    return channel


# ── E2E Response Fixtures ─────────────────────────────────────────

@pytest.fixture
def e2e_agent_success_response():
    """Resposta de sucesso do agent."""
    response = MagicMock()
    response.status = "success"
    response.content = """
    **Servidor Público Federal**

    Os servidores públicos federais são regidos pela Lei nº 8.112/1990.

    **Principais características:**
    - Cargo público de provimento efetivo
    - Regime jurídico único
    - Estabilidade após 3 anos
    """
    response.messages = [
        {"role": "user", "content": "Qual é o regime jurídico?"},
        {"role": "assistant", "content": response.content},
    ]
    response.is_paused = False
    response.tools_requiring_confirmation = []
    response.reasoning_content = None
    return response


@pytest.fixture
def e2e_agent_paused_response():
    """Resposta pausada do agent (requer confirmação)."""
    tool_mock = MagicMock()
    tool_mock.tool_name = "search_legislation"
    tool_mock.confirmed = None

    response = MagicMock()
    response.status = "paused"
    response.content = "Preciso pesquisar legislação recente"
    response.messages = []
    response.is_paused = True
    response.tools_requiring_confirmation = [tool_mock]
    response.reasoning_content = "User asked about recent legislation"
    return response


@pytest.fixture
def e2e_agent_error_response():
    """Resposta de erro do agent."""
    response = MagicMock()
    response.status = "error"
    response.content = "Erro ao processar requisição"
    response.messages = []
    response.is_paused = False
    response.tools_requiring_confirmation = []
    return response


@pytest.fixture
def e2e_agent_long_response():
    """Resposta longa do agent (teste de split)."""
    long_text = "\n\n".join([f"**Item {i}**: Conteúdo extenso sobre o tema." for i in range(1, 50)])
    response = MagicMock()
    response.status = "success"
    response.content = long_text
    response.messages = [{"role": "assistant", "content": long_text}]
    response.is_paused = False
    response.tools_requiring_confirmation = []
    response.reasoning_content = None
    return response


# ── E2E RAG Fixtures ─────────────────────────────────────────────

@pytest.fixture
def e2e_rag_context():
    """Contexto RAG mockado."""
    return """
    [CONTEXTO LEGISLATIVO RELEVANTE]
    [Fonte 1 (ano: 1988, banca: Cebraspe, tipo: CF, sim: 0.95)]
    Art. 37 da Constituição Federal: A administração pública direta e indireta de qualquer dos Poderes da União, dos Estados, do Distrito Federal e dos Municípios obedecerá aos princípios de LEGALIDADE, IMPESSOALIDADE, MORALIDADE, PUBLICIDADE e EFICIÊNCIA.

    [Fonte 2 (ano: 1990, banca: FCC, tipo: Lei, sim: 0.87)]
    Lei nº 8.112/1990: Dispõe sobre o regime jurídico dos servidores públicos civis da União, das autarquias e das fundações públicas federais.
    """


# ── E2E Database Fixtures ────────────────────────────────────────

@pytest.fixture
def e2e_session_history():
    """Histórico de sessão mockado."""
    return [
        {"role": "user", "content": "Olá"},
        {"role": "assistant", "content": "Olá! Como posso ajudar?"},
        {"role": "user", "content": "Quais são os princípios da admin?"},
        {"role": "assistant", "content": "LIME"},
    ]


# ── E2E HITL Fixtures ───────────────────────────────────────────

@pytest.fixture
def e2e_confirmation_view_confirmed():
    """View de confirmação com resultado True."""
    view = ConfirmationView()
    view.value = True
    view.stop = Mock()
    return view


@pytest.fixture
def e2e_confirmation_view_cancelled():
    """View de confirmação com resultado False."""
    view = ConfirmationView()
    view.value = False
    view.stop = Mock()
    return view


@pytest.fixture
def e2e_confirmation_view_timeout():
    """View de confirmação com timeout."""
    view = ConfirmationView()
    view.value = None
    view.wait = AsyncMock(return_value=True)  # Timeout retorna True no discord.py
    view.stop = Mock()
    return view
