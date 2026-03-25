#!/usr/bin/env python3
"""
Teste E2E Manual para OraculoBOT Discord

Este script permite testar o bot Discord com API real de forma interativa.
Útil para validar funcionalidades manualmente antes/depois de deploys.

┌─────────────────────────────────────────────────────────────────────────────┐
│ USO                                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. Modo interativo (padrão):                                               │
│     $ python scripts/test_e2e_manual.py                                     │
│                                                                             │
│  2. Modo dry-run (valida config sem iniciar bot):                           │
│     $ python scripts/test_e2e_manual.py --dry-run                            │
│                                                                             │
│  3. Testar em guild/channel específicos:                                    │
│     $ python scripts/test_e2e_manual.py --guild 123 --channel 456            │
│                                                                             │
│  4. Log detalhado:                                                           │
│     $ python scripts/test_e2e_manual.py --verbose                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ VARIÁVEIS DE AMBIENTE REQUERIDAS                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DISCORD_BOT_TOKEN      - Token do bot Discord (obrigatório)                │
│  DEEPSEEK_API_KEY       - Chave API DeepSeek (obrigatório)                  │
│  GEMINI_API_KEY         - Embeddings RAG (opcional)                         │
│  OPENAI_API_KEY         - Embeddings alternativos (opcional)                │
│  SUPABASE_DB_URL        - PostgreSQL persistente (opcional)                 │
│  TARGET_GUILD_ID        - Guild ID (default: 1283924742851661844)           │
│  TARGET_CHANNEL_ID      - Channel ID (default: 1486301006659715143)         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ DURANTE O TESTE                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. Bot inicia e aguarda mensagens no canal configurado                      │
│  2. Todas as interações são logadas (input/output)                           │
│  3. Use Ctrl+C para encerrar gracefully                                     │
│  4. Logs são salvos em logs/test_e2e_manual_{timestamp}.log                  │
│                                                                             │
│  Casos de teste sugeridos:                                                   │
│  • Mensagem simples de texto                                                │
│  • Upload de imagem (jpg, png)                                              │
│  • Upload de vídeo (mp4, mov)                                               │
│  • Upload de áudio (mp3, wav)                                               │
│  • Upload de PDF/documento                                                  │
│  • Mensagens em threads existentes                                          │
│  • Múltiplas mensagens consecutivas (histórico)                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import discord
from agno.agent.agent import Agent
from agno.utils.log import log_info, log_error, log_exception, log_warning

# Adiciona projeto ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from oraculo_bot.config import (
    DISCORD_BOT_TOKEN,
    DEEPSEEK_API_KEY,
    GEMINI_API_KEY,
    OPENAI_API_KEY,
    SUPABASE_DB_URL,
    TARGET_GUILD_ID,
    TARGET_CHANNEL_ID,
)
from oraculo_bot.db import SessionDAO
from oraculo_bot.agent import create_agent


class E2ETestBot(discord.Client):
    """Bot Discord wrapper para testes E2E com logging detalhado."""

    def __init__(
        self,
        guild_id: int,
        channel_id: int,
        agent: Agent,
        log_file: Optional[Path] = None,
    ):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.messages = True
        intents.message_content = True
        super().__init__(intents=intents)

        self.guild_id = guild_id
        self.channel_id = channel_id
        self.agent = agent
        self.log_file = log_file
        self.message_count = 0
        self.test_start_time = datetime.now()

        # Configura logger de arquivo
        if log_file:
            self.file_handler = logging.FileHandler(log_file, encoding="utf-8")
            self.file_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            self.file_handler.setFormatter(formatter)

            # Cria logger específico para o bot
            self.test_logger = logging.getLogger("e2e_test")
            self.test_logger.addHandler(self.file_handler)
            self.test_logger.setLevel(logging.INFO)
        else:
            self.test_logger = None

        self._register_events()

    def _is_target_channel(self, channel: discord.abc.Messageable) -> bool:
        """Verifica se o canal é o alvo ou thread filha."""
        if isinstance(channel, discord.TextChannel):
            return channel.id == self.channel_id
        if isinstance(channel, discord.Thread):
            return channel.parent_id == self.channel_id
        return False

    def _log_interaction(
        self,
        event_type: str,
        message: discord.Message,
        response: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        """Loga interação no console e arquivo."""
        self.message_count += 1

        # Metadata
        meta_parts = []
        if metadata:
            for key, value in metadata.items():
                meta_parts.append(f"{key}={value}")

        meta_str = " | " + " | ".join(meta_parts) if meta_parts else ""

        # Console log
        log_info(
            f"[{self.message_count:03d}] {event_type}: "
            f"{message.author.name}: {message.content[:100]}{meta_str}"
        )

        # File log (detalhado)
        if self.test_logger:
            self.test_logger.info(
                f"=== {event_type} #{self.message_count} ===\n"
                f"Author: {message.author.name} ({message.author.id})\n"
                f"Channel: {message.channel.name} ({message.channel.id})\n"
                f"Thread: {getattr(message.channel, 'name', 'N/A')}\n"
                f"Content: {message.content}\n"
                f"Attachments: {len(message.attachments)}\n"
                f"Timestamp: {message.created_at}\n"
                f"{meta_str}\n"
            )

            if response:
                self.test_logger.info(f"Bot Response:\n{response}\n")

    def _register_events(self) -> None:
        @self.event
        async def on_ready() -> None:
            guild = self.get_guild(self.guild_id)
            channel = self.get_channel(self.channel_id)

            log_info("=" * 70)
            log_info("🤖 OraculoBOT E2E Test Started")
            log_info("=" * 70)
            log_info(f"Bot logged in as: {self.user}")
            log_info(f"Target guild: {guild.name if guild else 'NOT FOUND'} (ID: {self.guild_id})")
            log_info(f"Target channel: {channel.name if channel else 'NOT FOUND'} (ID: {self.channel_id})")

            if self.test_logger:
                self.test_logger.info(
                    f"\n{'='*70}\n"
                    f"E2E TEST SESSION STARTED\n"
                    f"Start Time: {self.test_start_time.isoformat()}\n"
                    f"Bot: {self.user}\n"
                    f"Guild: {guild.name if guild else 'NOT FOUND'} ({self.guild_id})\n"
                    f"Channel: {channel.name if channel else 'NOT FOUND'} ({self.channel_id})\n"
                    f"{'='*70}\n"
                )

            # Validações
            if not guild:
                log_error(f"❌ Guild ID {self.guild_id} not found!")
            if not channel:
                log_error(f"❌ Channel ID {self.channel_id} not found!")

            log_info("✓ Bot ready and listening for messages...")
            log_info("Press Ctrl+C to stop gracefully")
            log_info("=" * 70)

        @self.event
        async def on_message(message: discord.Message) -> None:
            # Ignora próprias mensagens
            if message.author == self.user:
                return

            # Filtro de guild
            if not message.guild or message.guild.id != self.guild_id:
                return

            # Filtro de canal/thread
            if not self._is_target_channel(message.channel):
                return

            # Log da mensagem recebida
            attachment_info = {}
            if message.attachments:
                att = message.attachments[0]
                attachment_info = {
                    "media_type": att.content_type or "unknown",
                    "media_url": att.url,
                    "media_size": f"{att.size / 1024:.1f}KB",
                }

            self._log_interaction(
                "MESSAGE_RECEIVED",
                message,
                metadata=attachment_info if attachment_info else None,
            )

            # Processa mensagem (igual bot.py)
            await self._process_message(message)

        @self.event
        async def on_disconnect() -> None:
            if self.test_logger:
                self.test_logger.info("\n" + "=" * 70 + "\nBOT DISCONNECTED\n")

    async def _process_message(self, message: discord.Message) -> None:
        """Processa mensagem com logging detalhado."""
        from oraculo_bot.agent import initialize_session, get_session_history, enrich_with_rag
        from oraculo_bot.config import THREAD_NAME_PREFIX
        from textwrap import dedent

        # Thread management
        if isinstance(message.channel, discord.Thread):
            thread = message.channel
        elif isinstance(message.channel, discord.TextChannel):
            thread = await message.create_thread(
                name=f"{THREAD_NAME_PREFIX} {message.author.name}"
            )
        else:
            log_error(f"Unsupported channel type: {type(message.channel)}")
            return

        # Sessão
        session = initialize_session(str(thread.id), str(message.author.id), mode="estudo")
        history = get_session_history(str(thread.id))

        # Contexto
        context = dedent(f"""
            Discord username: {message.author.name}
            Discord userid: {message.author.id}
            Discord url: {message.jump_url}
            Session mode: {session.mode}
            Previous messages count: {len(history)}
        """)

        # RAG
        rag_context = enrich_with_rag(message.content, top_k=3)

        # Mídia
        import requests
        from agno.media import Audio, File, Image, Video

        media_kwargs = {}
        if message.attachments:
            att = message.attachments[0]
            mime = att.content_type or ""
            url = att.url

            if mime.startswith("image/"):
                media_kwargs["images"] = [Image(url=url)]
            elif mime.startswith("video/"):
                media_kwargs["videos"] = [Video(content=requests.get(url, timeout=30).content)]
            elif mime.startswith("audio/"):
                media_kwargs["audio"] = [Audio(url=url)]
            elif mime.startswith("application/"):
                media_kwargs["files"] = [File(content=requests.get(url, timeout=30).content)]

        # Executa agent
        async with thread.typing():
            full_context = context + rag_context
            self.agent.additional_context = full_context  # type: ignore

            response = await self.agent.arun(
                input=message.content,
                user_id=message.author.id,
                session_id=str(thread.id),
                **media_kwargs,
            )

            if response.status == "ERROR":
                log_error(f"Agent error: {response.content}")
                response.content = "Desculpe, ocorreu um erro. Tente novamente."

            # Salva histórico
            if hasattr(response, "messages") and response.messages:
                from oraculo_bot.agent import save_session_history
                save_session_history(str(thread.id), response.messages)

            # Extrai texto da resposta
            from agno.utils.message import get_text_from_message
            content = (
                get_text_from_message(response.content)
                if response.content is not None
                else ""
            )

            # Envia resposta
            await self._send_response(thread, f"<@{message.author.id}> {content}")

            # Log da resposta
            self._log_interaction(
                "BOT_RESPONSE",
                message,
                response=content,
                metadata={"status": response.status, "thread_id": thread.id},
            )

    async def _send_response(
        self,
        channel: discord.TextChannel | discord.Thread,
        message: str,
    ) -> None:
        """Envia mensagem com split automático."""
        from oraculo_bot.config import MAX_MESSAGE_LENGTH

        text = message.strip()
        if not text:
            return

        if len(text) <= MAX_MESSAGE_LENGTH:
            await channel.send(text)
            return

        # Calcula tamanho máximo considerando prefixo "[N/M] "
        # Prefixo máximo: "[999/999] " = 12 caracteres
        prefix_max_len = 12
        chunk_size = MAX_MESSAGE_LENGTH - prefix_max_len

        # Primeira passagem: divide em chunks
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunks.append(text[i : i + chunk_size])

        # Segunda passagem: adiciona prefixo e verifica tamanho
        for idx, chunk in enumerate(chunks, 1):
            prefix = f"[{idx}/{len(chunks)}] "
            message = f"{prefix}{chunk}"
            # Se ainda exceder, corta o chunk
            if len(message) > MAX_MESSAGE_LENGTH:
                allowed_chunk_size = MAX_MESSAGE_LENGTH - len(prefix)
                chunk = chunk[:allowed_chunk_size]
                message = f"{prefix}{chunk}"
            await channel.send(message)


def validate_environment() -> dict[str, bool]:
    """Valida variáveis de ambiente obrigatórias e opcionais."""
    results = {
        "required": {},
        "optional": {},
    }

    # Obrigatórias
    required_vars = {
        "DISCORD_BOT_TOKEN": DISCORD_BOT_TOKEN,
        "DEEPSEEK_API_KEY": DEEPSEEK_API_KEY,
    }

    for name, value in required_vars.items():
        is_set = bool(value)
        results["required"][name] = is_set
        if is_set:
            log_info(f"✓ {name}: {'*' * 10}")  # Mask value
        else:
            log_error(f"✗ {name}: NOT SET")

    # Opcionais
    optional_vars = {
        "GEMINI_API_KEY": GEMINI_API_KEY,
        "OPENAI_API_KEY": OPENAI_API_KEY,
        "SUPABASE_DB_URL": SUPABASE_DB_URL,
    }

    for name, value in optional_vars.items():
        is_set = bool(value)
        results["optional"][name] = is_set
        status = "✓" if is_set else "○"
        log_info(f"{status} {name}: {'SET' if is_set else 'NOT SET (optional)'}")

    return results


def parse_args() -> argparse.Namespace:
    """Parse argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Teste E2E manual para OraculoBOT Discord",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Valida configuração sem iniciar o bot",
    )

    parser.add_argument(
        "--guild",
        type=int,
        default=TARGET_GUILD_ID,
        help=f"Guild ID (default: {TARGET_GUILD_ID})",
    )

    parser.add_argument(
        "--channel",
        type=int,
        default=TARGET_CHANNEL_ID,
        help=f"Channel ID (default: {TARGET_CHANNEL_ID})",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Log detalhado (debug)",
    )

    return parser.parse_args()


def main() -> int:
    """Entrypoint."""
    args = parse_args()

    # Configura logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    log_info("=" * 70)
    log_info("🧪 OraculoBOT E2E Manual Test")
    log_info("=" * 70)

    # Valida ambiente
    log_info("\n📋 Validando variáveis de ambiente...")
    env_results = validate_environment()

    missing_required = [k for k, v in env_results["required"].items() if not v]
    if missing_required:
        log_error(f"\n❌ Variáveis obrigatórias faltando: {', '.join(missing_required)}")
        log_error("Consulte .env.example para configuração")
        return 1

    log_info("\n✓ Ambiente OK")

    # Dry-run
    if args.dry_run:
        log_info("\n✓ Dry-run concluído - configuração válida")
        return 0

    # Inicializa banco
    log_info("\n📦 Inicializando banco de dados...")
    try:
        dao = SessionDAO()
        dao.init_db()
        log_info("✓ Banco OK")
    except Exception as e:
        log_exception(e)
        log_error("✗ Falha ao inicializar banco")
        return 1

    # Limpa sessões antigas
    try:
        dao.cleanup_old_sessions(30)
        log_info("✓ Sessões antigas limpas")
    except Exception as e:
        log_exception(e)
        log_warning("⚠ Falha ao limpar sessões antigas (não crítico)")

    # Cria agent
    log_info("\n🤖 Inicializando agent...")
    try:
        agent = create_agent()
        log_info(f"✓ Agent criado: {agent.name}")
    except Exception as e:
        log_exception(e)
        log_error("✗ Falha ao criar agent")
        return 1

    # Cria diretório de logs
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Arquivo de log
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"test_e2e_manual_{timestamp}.log"

    # Inicia bot
    log_info(f"\n🚀 Iniciando bot de teste...")
    log_info(f"📝 Log file: {log_file}")
    log_info(f"🎯 Guild: {args.guild}")
    log_info(f"🎯 Channel: {args.channel}")

    try:
        bot = E2ETestBot(
            guild_id=args.guild,
            channel_id=args.channel,
            agent=agent,
            log_file=log_file,
        )
        bot.run(DISCORD_BOT_TOKEN)
    except KeyboardInterrupt:
        log_info("\n\n🛑 Interrupção pelo usuário")
    except Exception as e:
        log_exception(e)
        log_error("✗ Falha ao executar bot")
        return 1
    finally:
        if bot is not None and hasattr(bot, 'test_logger') and bot.test_logger:
            bot.test_logger.info(
                f"\n{'='*70}\n"
                f"E2E TEST SESSION ENDED\n"
                f"End Time: {datetime.now().isoformat()}\n"
                f"Total Messages: {bot.message_count}\n"
                f"Duration: {datetime.now() - bot.test_start_time}\n"
                f"{'='*70}\n"
            )
            bot.file_handler.close()

    log_info("✓ Teste concluído")
    return 0


if __name__ == "__main__":
    sys.exit(main())
