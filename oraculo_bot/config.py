"""Configuração centralizada via variáveis de ambiente."""

from __future__ import annotations

import os
from pathlib import Path

# Carregar .env se existir
try:
    from dotenv import load_dotenv

    _env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(_env_path)
except ImportError:
    pass


def _require_env(key: str) -> str:
    """Retorna o valor da env var ou levanta ValueError."""
    value = os.getenv(key)
    if not value:
        msg = f"Variável de ambiente '{key}' não definida. Consulte .env.example."
        raise ValueError(msg)
    return value


# ── Tokens (obrigatórios) ────────────────────────────────────
DISCORD_BOT_TOKEN: str = _require_env("DISCORD_BOT_TOKEN")

# ── LLM API ───────────────────────────────────────────────────
DEEPSEEK_API_KEY: str = _require_env("DEEPSEEK_API_KEY")
GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")  # Para embeddings RAG (grátis)
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")  # Opcional - embeddings alternativos

# ── IDs do Discord ───────────────────────────────────────────
TARGET_GUILD_ID: int = int(os.getenv("TARGET_GUILD_ID", "1283924742851661844"))
TARGET_CHANNEL_ID: int = int(os.getenv("TARGET_CHANNEL_ID", "1486301006659715143"))

# ── LLM ──────────────────────────────────────────────────────
MODEL_ID: str = os.getenv("MODEL_ID", "deepseek-chat")
HISTORY_RUNS: int = int(os.getenv("HISTORY_RUNS", "5"))

# ── Discord ──────────────────────────────────────────────────
MAX_MESSAGE_LENGTH: int = 1500
THREAD_NAME_PREFIX: str = "💬"
ERROR_MESSAGE: str = "Desculpe, ocorreu um erro. Tente novamente."

# ── Banco de Dados ────────────────────────────────────────────
SUPABASE_DB_URL: str | None = os.getenv("SUPABASE_DB_URL")
