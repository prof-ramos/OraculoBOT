"""Core do bot Discord — filtro de guild/channel, threading, mídia, menção."""

from __future__ import annotations

from textwrap import dedent
from typing import Optional, Union

import discord
import requests
from agno.agent.agent import Agent, RunOutput
from agno.media import Audio, File, Image, Video
from agno.team.team import Team, TeamRunOutput
from agno.utils.log import log_error, log_info
from agno.utils.message import get_text_from_message

from oraculo_bot.config import (
    DISCORD_BOT_TOKEN,
    ERROR_MESSAGE,
    MAX_MESSAGE_LENGTH,
    TARGET_CHANNEL_ID,
    TARGET_GUILD_ID,
    THREAD_NAME_PREFIX,
)
from oraculo_bot.agent import initialize_session, save_session_history, get_session_history, enrich_with_rag
from oraculo_bot.views import ConfirmationView


class OracleDiscordBot:
    """Bot Discord filtrado por guild/channel. Responde sem menção, cita o autor."""

    def __init__(
        self,
        agent: Optional[Agent] = None,
        team: Optional[Team] = None,
        *,
        guild_id: int = TARGET_GUILD_ID,
        channel_id: int = TARGET_CHANNEL_ID,
    ) -> None:
        if not agent and not team:
            msg = "Forneça 'agent' ou 'team'."
            raise ValueError(msg)

        self.agent = agent
        self.team = team
        self.guild_id = guild_id
        self.channel_id = channel_id

        intents = discord.Intents.all()
        self.client = discord.Client(intents=intents)
        self._register_events()

    # ── Helpers ───────────────────────────────────────────────

    def _is_target_channel(self, channel: discord.abc.Messageable) -> bool:
        """Retorna True se o canal é o alvo ou uma thread filha dele."""
        if isinstance(channel, discord.TextChannel):
            return channel.id == self.channel_id
        if isinstance(channel, discord.Thread):
            return channel.parent_id == self.channel_id
        return False

    @staticmethod
    def _extract_media(
        message: discord.Message,
    ) -> tuple[
        Optional[str],
        Optional[bytes],
        Optional[str],
        Optional[bytes],
        Optional[str],
    ]:
        """Extrai o primeiro attachment classificado por tipo MIME.

        Returns:
            (image_url, video_bytes, audio_url, file_bytes, media_url)
        """
        if not message.attachments:
            return None, None, None, None, None

        attachment = message.attachments[0]
        mime = attachment.content_type or ""
        url = attachment.url

        if mime.startswith("image/"):
            return url, None, None, None, url
        if mime.startswith("video/"):
            return None, requests.get(url, timeout=30).content, None, None, url
        if mime.startswith("audio/"):
            return None, None, url, None, url
        if mime.startswith("application/"):
            return None, None, None, requests.get(url, timeout=30).content, url

        return None, None, None, None, url

    @staticmethod
    def _build_media_kwargs(
        image: Optional[str],
        video: Optional[bytes],
        audio: Optional[str],
        file: Optional[bytes],
    ) -> dict:
        """Monta dict de mídia para agent.arun()."""
        kwargs: dict = {}
        if image:
            kwargs["images"] = [Image(url=image)]
        if video:
            kwargs["videos"] = [Video(content=video)]
        if audio:
            kwargs["audio"] = [Audio(url=audio)]
        if file:
            kwargs["files"] = [File(content=file)]
        return kwargs

    # ── Events ───────────────────────────────────────────────

    def _register_events(self) -> None:
        @self.client.event
        async def on_ready() -> None:
            log_info(f"Bot conectado como {self.client.user}")
            log_info(f"Escutando guild={self.guild_id} channel={self.channel_id}")

        @self.client.event
        async def on_message(message: discord.Message) -> None:
            if message.author == self.client.user:
                return
            if not message.guild or message.guild.id != self.guild_id:
                return
            if not self._is_target_channel(message.channel):
                return

            await self._process_message(message)

    async def _process_message(self, message: discord.Message) -> None:
        """Pipeline completo: mídia → thread → agent → resposta."""
        img, vid, aud, fil, media_url = self._extract_media(message)
        user_name = message.author.name
        user_id = message.author.id

        log_info(f"[{user_name}] {message.content} | media={media_url}")

        # Thread management
        if isinstance(message.channel, discord.Thread):
            thread = message.channel
        elif isinstance(message.channel, discord.TextChannel):
            thread = await message.create_thread(
                name=f"{THREAD_NAME_PREFIX} {user_name}"
            )
        else:
            log_info(f"Canal não suportado: {type(message.channel)}")
            return

        mention = f"<@{user_id}>"

        # Inicializa sessão no banco
        session = initialize_session(str(thread.id), str(user_id), mode="estudo")

        # Carrega histórico anterior
        history = get_session_history(str(thread.id))

        context = dedent(f"""
            Discord username: {user_name}
            Discord userid: {user_id}
            Discord url: {message.jump_url}
            Session mode: {session.mode}
            Previous messages count: {len(history)}
        """)

        # Enriquece com legislação relevante via RAG
        rag_context = enrich_with_rag(message.content, top_k=3)

        media_kwargs = self._build_media_kwargs(img, vid, aud, fil)

        async with thread.typing():
            runner = self.agent or self.team

            # Adiciona contexto RAG ao context existente
            full_context = context + rag_context

            runner.additional_context = full_context  # type: ignore[union-attr]

            response = await runner.arun(  # type: ignore[union-attr]
                input=message.content,
                user_id=user_id,
                session_id=str(thread.id),
                **media_kwargs,
            )

            if response.status == "ERROR":
                log_error(response.content)
                response.content = ERROR_MESSAGE

            # Salva histórico após execução
            if hasattr(response, 'messages') and response.messages:
                save_session_history(str(thread.id), response.messages)

            await self._handle_response(response, thread, mention)

    # ── Response handling ────────────────────────────────────

    async def _handle_hitl(
        self,
        response: RunOutput,
        thread: Union[discord.Thread, discord.TextChannel],
    ) -> RunOutput:
        """Human-in-the-Loop: pede confirmação via botões antes de executar tools."""
        if not response.is_paused:
            return response

        for tool in response.tools_requiring_confirmation:
            view = ConfirmationView()
            await thread.send(
                f"🔧 Tool requer confirmação: **{tool.tool_name}**",
                view=view,
            )
            await view.wait()
            tool.confirmed = view.value if view.value is not None else False

        if self.agent:
            response = await self.agent.acontinue_run(run_response=response)

        return response

    async def _handle_response(
        self,
        response: Union[RunOutput, TeamRunOutput],
        thread: Union[discord.TextChannel, discord.Thread],
        mention: str,
    ) -> None:
        """Processa resposta e envia ao Discord com menção."""
        if isinstance(response, RunOutput):
            response = await self._handle_hitl(response, thread)

        if response.reasoning_content:
            log_info(f"[Reasoning] {response.reasoning_content[:200]}...")

        content = (
            get_text_from_message(response.content)
            if response.content is not None
            else ""
        )
        await self._send_messages(thread, f"{mention} {content}")

    async def _send_messages(
        self,
        thread: Union[discord.TextChannel, discord.Thread],
        message: str,
    ) -> None:
        """Envia mensagem com split automático para textos longos."""
        text = message.strip()
        if not text:
            return

        if len(text) <= MAX_MESSAGE_LENGTH:
            await thread.send(text)
            return

        batches = [
            text[i : i + MAX_MESSAGE_LENGTH]
            for i in range(0, len(text), MAX_MESSAGE_LENGTH)
        ]
        for idx, batch in enumerate(batches, 1):
            await thread.send(f"[{idx}/{len(batches)}] {batch}")

    # ── Entrypoint ───────────────────────────────────────────

    def serve(self) -> None:
        """Inicia o bot."""
        self.client.run(DISCORD_BOT_TOKEN)
