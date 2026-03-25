"""Entrypoint: python -m oraculo_bot."""

import logging

from oraculo_bot.agent import create_agent
from oraculo_bot.bot import OracleDiscordBot
from oraculo_bot.db import SessionDAO

logger = logging.getLogger(__name__)


def main() -> None:
    # Inicializa banco de dados
    try:
        dao = SessionDAO()
        dao.init_db()
    except Exception:
        logger.exception("Erro ao inicializar DB")
        raise

    # Limpa sessões antigas
    try:
        dao.cleanup_old_sessions(30)
    except Exception:
        logger.exception("Erro ao limpar sessões antigas")

    # Inicia bot
    agent = create_agent()
    bot = OracleDiscordBot(agent=agent)
    bot.serve()


if __name__ == "__main__":
    main()
