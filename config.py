"""Configuração centralizada via variáveis de ambiente."""

from __future__ import annotations

import os


def _require_env(key: str) -> str:
    """Retorna o valor da env var ou levanta ValueError."""
    value = os.getenv(key)
    if not value:
        msg = f"Variável de ambiente '{key}' não definida. Consulte .env.example."
        raise ValueError(msg)
    return value


# ── Tokens (obrigatórios) ────────────────────────────────────
DISCORD_BOT_TOKEN: str = _require_env("DISCORD_BOT_TOKEN")

# ── IDs do Discord ───────────────────────────────────────────
TARGET_GUILD_ID: int = int(os.getenv("TARGET_GUILD_ID", "1283924742851661844"))
TARGET_CHANNEL_ID: int = int(os.getenv("TARGET_CHANNEL_ID", "1486301006659715143"))

# ── LLM ──────────────────────────────────────────────────────
MODEL_ID: str = os.getenv("MODEL_ID", "gpt-4.1")
HISTORY_RUNS: int = int(os.getenv("HISTORY_RUNS", "5"))

# ── Discord ──────────────────────────────────────────────────
MAX_MESSAGE_LENGTH: int = 1500
THREAD_NAME_PREFIX: str = "💬"
ERROR_MESSAGE: str = "Desculpe, ocorreu um erro. Tente novamente."
