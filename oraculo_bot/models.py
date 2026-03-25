"""Modelos de dados do OraculoBOT."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, String, create_engine, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base declarativa para modelos ORM."""


class DiscordSession(Base):
    """Sessao de conversa do bot no Discord.

    Mapeia para a tabela 'discord_sessions' no PostgreSQL.
    """

    __tablename__ = "discord_sessions"

    # Identificadores
    thread_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Metadados da sessao
    mode: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="estudo",
        comment="Modo de operacao: estudo, professor, simulado, casual"
    )

    # Dados da sessao (JSONB para flexibilidade)
    session_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Dados da sessao: historico, estado, etc."
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP")
    )

    def __repr__(self) -> str:
        return f"<DiscordSession(thread_id={self.thread_id}, user_id={self.user_id}, mode={self.mode})>"


def create_tables(db_url: str) -> None:
    """Cria as tabelas no banco de dados.

    Args:
        db_url: URL de conexao PostgreSQL.
    """
    engine = create_engine(db_url)
    try:
        Base.metadata.create_all(engine)
    finally:
        engine.dispose()
