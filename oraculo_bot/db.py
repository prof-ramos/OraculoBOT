"""Camada de acesso a dados do OraculoBOT."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import create_engine, delete, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from oraculo_bot.config import SUPABASE_DB_URL
from oraculo_bot.models import Base, DiscordSession, create_tables

logger = logging.getLogger(__name__)


class SessionDAO:
    """DAO para gerenciar sessoes Discord no PostgreSQL.

    UNICA camada de persistencia do sistema.
    Fallback para memoria quando DB nao disponivel.
    """

    def __init__(self, db_url: Optional[str] = None):
        """Inicializa o DAO com a URL do banco.

        Args:
            db_url: URL de conexao PostgreSQL. Se None, usa SUPABASE_DB_URL.
        """
        self.db_url = db_url or SUPABASE_DB_URL
        self._engine = None
        # Fallback de memoria quando DB nao disponivel
        self._memory_store: dict[str, DiscordSession] = {}

    @property
    def engine(self) -> Engine:
        """Lazy initialization da engine."""
        if self._engine is None:
            if not self.db_url:
                raise RuntimeError("SUPABASE_DB_URL nao configurada")
            self._engine = create_engine(self.db_url)
        return self._engine

    @property
    def enabled(self) -> bool:
        """Verifica se a persistencia esta habilitada."""
        return bool(self.db_url)

    def init_db(self) -> None:
        """Inicializa o banco de dados (cria tabelas).

        Trata erros de conexao e fallback para memoria.
        """
        if self.enabled:
            try:
                create_tables(self.db_url)
                logger.info("Tabelas criadas com sucesso no PostgreSQL")
            except Exception as e:
                logger.warning(f"Falha ao conectar PostgreSQL: {e}. Usando memoria.")
                self.db_url = None

    def get_session(self, thread_id: str) -> Optional[DiscordSession]:
        """Retorna uma sessao pelo thread_id.

        Args:
            thread_id: ID do thread Discord.

        Returns:
            A sessao encontrada ou None.
        """
        if not self.enabled:
            return self._memory_store.get(thread_id)

        try:
            with Session(self.engine) as session:
                stmt = select(DiscordSession).where(DiscordSession.thread_id == thread_id)
                return session.scalar(stmt)
        except Exception as e:
            logger.error(f"Erro ao buscar sessao: {e}. Usando memoria.")
            return self._memory_store.get(thread_id)

    def create_session(
        self,
        thread_id: str,
        user_id: str,
        mode: str = "estudo",
        session_data: Optional[dict] = None,
    ) -> DiscordSession:
        """Cria uma nova sessao.

        Args:
            thread_id: ID do thread Discord.
            user_id: ID do usuario Discord.
            mode: Modo de operacao.
            session_data: Dados iniciais da sessao.

        Returns:
            A sessao criada.
        """
        discord_session = DiscordSession(
            thread_id=thread_id,
            user_id=user_id,
            mode=mode,
            session_data=session_data or {},
        )

        if not self.enabled:
            self._memory_store[thread_id] = discord_session
            return discord_session

        try:
            with Session(self.engine) as session:
                session.add(discord_session)
                session.commit()
                session.refresh(discord_session)
                return discord_session
        except Exception as e:
            logger.error(f"Erro ao criar sessao: {e}. Usando memoria.")
            self._memory_store[thread_id] = discord_session
            return discord_session

    def update_session_data(self, thread_id: str, session_data: dict) -> Optional[DiscordSession]:
        """Atualiza os dados de uma sessao.

        Args:
            thread_id: ID do thread Discord.
            session_data: Novos dados da sessao (sera mergido com existente).

        Returns:
            A sessao atualizada ou None se nao encontrada.
        """
        if not self.enabled:
            if thread_id in self._memory_store:
                self._memory_store[thread_id].session_data.update(session_data)
                return self._memory_store[thread_id]
            return None

        try:
            with Session(self.engine) as session:
                stmt = select(DiscordSession).where(DiscordSession.thread_id == thread_id)
                discord_session = session.scalar(stmt)

                if discord_session:
                    # Merge dos dados existentes com novos
                    discord_session.session_data.update(session_data)
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(discord_session, "session_data")
                    session.commit()
                    session.refresh(discord_session)

                return discord_session
        except Exception as e:
            logger.error(f"Erro ao atualizar sessao: {e}.")
            return None

    def get_or_create_session(
        self,
        thread_id: str,
        user_id: str,
        mode: str = "estudo",
    ) -> DiscordSession:
        """Retorna uma sessao existente ou cria uma nova.

        THREAD-SAFE: Usa INSERT ... ON CONFLICT para evitar race conditions.

        Args:
            thread_id: ID do thread Discord.
            user_id: ID do usuario Discord.
            mode: Modo de operacao (usado apenas na criacao).

        Returns:
            A sessao encontrada ou criada.
        """
        # Tenta buscar primeiro (em memoria ou DB)
        existing = self.get_session(thread_id)
        if existing:
            return existing

        # Thread-safe insert usando ON CONFLICT (apenas se DB habilitado)
        if self.enabled:
            try:
                with Session(self.engine) as session:
                    stmt = text("""
                        INSERT INTO discord_sessions (thread_id, user_id, mode, session_data)
                        VALUES (:thread_id, :user_id, :mode, :session_data)
                        ON CONFLICT (thread_id) DO NOTHING
                        RETURNING thread_id, user_id, mode, session_data, created_at, updated_at
                    """)
                    result = session.execute(stmt, {
                        "thread_id": thread_id,
                        "user_id": user_id,
                        "mode": mode,
                        "session_data": {},
                    })

                    if result.rowcount > 0:
                        row = result.fetchone()
                        session.commit()
                        return DiscordSession(
                            thread_id=row[0],
                            user_id=row[1],
                            mode=row[2],
                            session_data=row[3],
                            created_at=row[4],
                            updated_at=row[5],
                        )
                    else:
                        # Ja existia (race condition), busca novamente
                        session.rollback()
                        return self.get_session(thread_id) or self.create_session(
                            thread_id, user_id, mode
                        )
            except Exception as e:
                logger.error(f"Erro em get_or_create: {e}. Criando em memoria.")
                return self.create_session(thread_id, user_id, mode)
        else:
            return self.create_session(thread_id, user_id, mode)

    def cleanup_old_sessions(self, days: int = 30) -> int:
        """Remove sessoes antigas do banco.

        Args:
            days: Numero de dias para considerar uma sessao como antiga.

        Returns:
            Numero de sessoes removidas.
        """
        if not self.enabled:
            return 0

        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

            with Session(self.engine) as session:
                stmt = delete(DiscordSession).where(
                    DiscordSession.updated_at < cutoff_date
                )
                result = session.execute(stmt)
                count = result.rowcount
                session.commit()
                logger.info(f"Removidas {count} sessoes antigas (> {days} dias)")
                return count
        except Exception as e:
            logger.error(f"Erro ao limpar sessoes antigas: {e}")
            return 0
