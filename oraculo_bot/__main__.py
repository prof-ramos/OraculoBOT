"""Entrypoint: python -m oraculo_bot."""

from oraculo_bot.agent import create_agent
from oraculo_bot.bot import OracleDiscordBot


def main() -> None:
    agent = create_agent()
    bot = OracleDiscordBot(agent=agent)
    bot.serve()


if __name__ == "__main__":
    main()
