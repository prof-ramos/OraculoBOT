"""Testes unitários para OracleDiscordBot."""

from unittest.mock import Mock, MagicMock, AsyncMock
import pytest

from oraculo_bot.bot import OracleDiscordBot
from oraculo_bot.config import TARGET_GUILD_ID, TARGET_CHANNEL_ID


# ── Testes de _is_target_channel ────────────────────────────────────

class TestIsTargetChannel:
    """Testes para _is_target_channel()."""

    def test_is_target_channel_returns_true_for_target_text_channel(self, mock_discord_text_channel):
        """Deve retornar True para canal alvo."""
        bot = OracleDiscordBot(agent=Mock())
        result = bot._is_target_channel(mock_discord_text_channel)
        assert result is True

    def test_is_target_channel_returns_true_for_child_thread(self, mock_discord_thread):
        """Deve retornar True para thread filha do canal alvo."""
        bot = OracleDiscordBot(agent=Mock())
        mock_discord_thread.parent_id = TARGET_CHANNEL_ID
        result = bot._is_target_channel(mock_discord_thread)
        assert result is True

    def test_is_target_channel_returns_false_for_different_channel(self, mocker):
        """Deve retornar False para canal diferente."""
        bot = OracleDiscordBot(agent=Mock())

        channel = MagicMock()
        channel.id = 999999999
        channel.type = 0  # TextChannel

        result = bot._is_target_channel(channel)
        assert result is False

    def test_is_target_channel_returns_false_for_orphan_thread(self, mocker):
        """Deve retornar False para thread órfã."""
        bot = OracleDiscordBot(agent=Mock())

        thread = MagicMock()
        thread.parent_id = 999999999
        thread.type = 11  # Thread

        result = bot._is_target_channel(thread)
        assert result is False


# ── Testes de _extract_media ──────────────────────────────────────────

class TestExtractMedia:
    """Testes para _extract_media()."""

    def test_extract_media_no_attachments(self):
        """Deve retornar Nones quando sem attachments."""
        message = Mock()
        message.attachments = []

        img, vid, aud, fil, url = OracleDiscordBot._extract_media(message)

        assert img is None
        assert vid is None
        assert aud is None
        assert fil is None
        assert url is None

    def test_extract_media_image(self, mocker):
        """Deve extrair URL de imagem."""
        message = Mock()
        message.attachments = [Mock()]

        attachment = message.attachments[0]
        attachment.content_type = "image/png"
        attachment.url = "https://example.com/image.png"

        img, vid, aud, fil, url = OracleDiscordBot._extract_media(message)

        assert img == "https://example.com/image.png"
        assert vid is None
        assert aud is None
        assert fil is None
        assert url == "https://example.com/image.png"

    def test_extract_media_video(self, mocker):
        """Deve baixar bytes de vídeo."""
        message = Mock()
        message.attachments = [Mock()]

        attachment = message.attachments[0]
        attachment.content_type = "video/mp4"
        attachment.url = "https://example.com/video.mp4"

        mock_get = mocker.patch("requests.get", return_value=Mock(content=b"video_bytes"))

        img, vid, aud, fil, url = OracleDiscordBot._extract_media(message)

        assert img is None
        assert vid == b"video_bytes"
        assert aud is None
        assert fil is None
        assert url == "https://example.com/video.mp4"
        mock_get.assert_called_once()

    def test_extract_media_audio(self, mocker):
        """Deve extrair URL de áudio."""
        message = Mock()
        message.attachments = [Mock()]

        attachment = message.attachments[0]
        attachment.content_type = "audio/mpeg"
        attachment.url = "https://example.com/audio.mp3"

        img, vid, aud, fil, url = OracleDiscordBot._extract_media(message)

        assert img is None
        assert vid is None
        assert aud == "https://example.com/audio.mp3"
        assert fil is None
        assert url == "https://example.com/audio.mp3"

    def test_extract_media_file(self, mocker):
        """Deve baixar bytes de arquivo."""
        message = Mock()
        message.attachments = [Mock()]

        attachment = message.attachments[0]
        attachment.content_type = "application/pdf"
        attachment.url = "https://example.com/file.pdf"

        mock_get = mocker.patch("requests.get", return_value=Mock(content=b"file_bytes"))

        img, vid, aud, fil, url = OracleDiscordBot._extract_media(message)

        assert img is None
        assert vid is None
        assert aud is None
        assert fil == b"file_bytes"
        assert url == "https://example.com/file.pdf"
        mock_get.assert_called_once()

    def test_extract_media_unknown_mime(self, mocker):
        """Deve retornar URL para MIME type desconhecido."""
        message = Mock()
        message.attachments = [Mock()]

        attachment = message.attachments[0]
        attachment.content_type = "unknown/type"
        attachment.url = "https://example.com/file.unknown"

        img, vid, aud, fil, url = OracleDiscordBot._extract_media(message)

        # Fallback: retorna URL
        assert url == "https://example.com/file.unknown"


# ── Testes de _build_media_kwargs ───────────────────────────────────

class TestBuildMediaKwargs:
    """Testes para _build_media_kwargs()."""

    def test_build_media_kwargs_empty(self):
        """Deve retornar dict vazio sem mídia."""
        kwargs = OracleDiscordBot._build_media_kwargs(
            image=None, video=None, audio=None, file=None
        )
        assert kwargs == {}

    def test_build_media_kwargs_image(self, mocker):
        """Deve criar Image para agno."""
        mocker.patch("oraculo_bot.bot.Image", return_value="image_obj")

        kwargs = OracleDiscordBot._build_media_kwargs(
            image="http://image.png", video=None, audio=None, file=None
        )

        assert "images" in kwargs
        assert len(kwargs["images"]) == 1

    def test_build_media_kwargs_video(self, mocker):
        """Deve criar Video para agno."""
        mocker.patch("oraculo_bot.bot.Video", return_value="video_obj")

        kwargs = OracleDiscordBot._build_media_kwargs(
            image=None, video=b"video_bytes", audio=None, file=None
        )

        assert "videos" in kwargs
        assert len(kwargs["videos"]) == 1

    def test_build_media_kwargs_audio(self, mocker):
        """Deve criar Audio para agno."""
        mocker.patch("oraculo_bot.bot.Audio", return_value="audio_obj")

        kwargs = OracleDiscordBot._build_media_kwargs(
            image=None, video=None, audio="http://audio.mp3", file=None
        )

        assert "audio" in kwargs
        assert len(kwargs["audio"]) == 1

    def test_build_media_kwargs_file(self, mocker):
        """Deve criar File para agno."""
        mocker.patch("oraculo_bot.bot.File", return_value="file_obj")

        kwargs = OracleDiscordBot._build_media_kwargs(
            image=None, video=None, audio=None, file=b"file_bytes"
        )

        assert "files" in kwargs
        assert len(kwargs["files"]) == 1


# ── Testes de _send_messages ─────────────────────────────────────────

class TestSendMessages:
    """Testes para _send_messages()."""

    @pytest.mark.asyncio
    async def test_send_messages_short_sends_directly(self):
        """Deve enviar mensagem curta diretamente."""
        bot = OracleDiscordBot(agent=Mock())
        thread = AsyncMock()
        message = "Mensagem curta"

        await bot._send_messages(thread, message)

        thread.send.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_messages_empty_returns_early(self):
        """Deve retornar cedo se mensagem vazia."""
        bot = OracleDiscordBot(agent=Mock())
        thread = AsyncMock()
        message = "   "

        await bot._send_messages(thread, message)

        # Não deve chamar send
        thread.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_messages_long_splits_correctly(self):
        """Deve splitar mensagem longa corretamente."""
        bot = OracleDiscordBot(agent=Mock())
        thread = AsyncMock()
        # Mensagem > 1500 chars
        message = "A" * 2000

        await bot._send_messages(thread, message)

        # Deve chamar send 2 vezes (1500 + 500)
        assert thread.send.call_count == 2

    @pytest.mark.asyncio
    async def test_send_messages_exact_boundary(self):
        """Deve enviar 1 mensagem se exatamente 1500 chars."""
        bot = OracleDiscordBot(agent=Mock())
        thread = AsyncMock()
        message = "A" * 1500

        await bot._send_messages(thread, message)

        thread.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_messages_batch_format(self):
        """Deve formatar batches com [N/M]."""
        bot = OracleDiscordBot(agent=Mock())
        thread = AsyncMock()
        message = "A" * 3000  # 2 batches

        await bot._send_messages(thread, message)

        calls = thread.send.call_args_list
        assert "[1/2]" in str(calls[0])
        assert "[2/2]" in str(calls[1])


# ── Testes de _handle_response ───────────────────────────────────────

class TestHandleResponse:
    """Testes para _handle_response()."""

    @pytest.mark.asyncio
    async def test_handle_response_with_mention(self, mock_discord_thread, mock_run_output, mocker):
        """Deve incluir menção na resposta."""
        bot = OracleDiscordBot(agent=Mock())
        mock_run_output.reasoning_content = None
        mocker.patch("oraculo_bot.bot.get_text_from_message", return_value="Response text")

        await bot._handle_response(
            mock_run_output,
            mock_discord_thread,
            "<@123456789>"
        )

        # Verificar se menção foi incluída
        mock_discord_thread.send.assert_called_once()
        call_args = str(mock_discord_thread.send.call_args)
        assert "<@123456789>" in call_args or "<@123456789>" in str(mock_discord_thread.send)


# ── Testes de _handle_hitl ─────────────────────────────────────────────

class TestHandleHITL:
    """Testes para Human-in-the-Loop."""

    @pytest.mark.asyncio
    async def test_handle_hitl_not_paused_returns_response(self, mock_discord_thread, mock_paused_agent_response, mocker):
        """Deve retornar response se não pausado."""
        bot = OracleDiscordBot(agent=Mock())
        mock_paused_agent_response.is_paused = False
        mocker.patch("oraculo_bot.bot.ConfirmationView", return_value=MagicMock())

        result = await bot._handle_hitl(
            mock_paused_agent_response,
            mock_discord_thread
        )

        assert result is mock_paused_agent_response

    @pytest.mark.asyncio
    async def test_handle_hitl_confirmed_continues(self, mock_discord_thread, mock_paused_agent_response, mocker):
        """Deve continuar run se confirmado."""
        bot = OracleDiscordBot(agent=Mock())
        bot.agent = Mock()
        mock_view = MagicMock()
        mock_view.value = True
        mock_view.wait = AsyncMock(return_value=True)
        mock_discord_thread.send = AsyncMock()
        mocker.patch("oraculo_bot.bot.ConfirmationView", return_value=mock_view)

        bot.agent.acontinue_run = AsyncMock(return_value=mock_paused_agent_response)

        result = await bot._handle_hitl(
            mock_paused_agent_response,
            mock_discord_thread
        )

        bot.agent.acontinue_run.assert_called_once()
