# Plano: Integracao Supabase PostgreSQL com OraculoBOT

**Data:** 2025-03-25
**Status:** ✅ APPROVED - ConsensusRalplan (Iteração 3)
**Complexidade:** MÉDIA
**Arquivos:** 5 arquivos a modificar + 2 novos

**Correções finais aplicadas:**
- Substituído `datetime.utcnow()` por `datetime.now(timezone.utc)` (Python 3.14+)

---

## Resumo Executivo

Este plano adiciona persistencia de sessoes PostgreSQL ao OraculoBOT usando o Supabase como backend. O historico de conversas atualmente armazenado apenas em memoria sera persistido, permitindo que o bot mantenha o contexto entre reinicializacoes.

**CORRECOES CRITICAS desta revisao (ITERAÇÃO 3):**
- Removida manipulacao invalida de `agent.memory.messages`
- Usando recursos nativos do Agno: `add_history_to_context=True` + `session_id`
- Adicionado hook em `bot.py` para salvar historico apos `arun()`
- Reutilizando instancia unica do Agent (padrao agent_factory removido)

---

## RALPLAN-DR: Princípios, Drivers e Opcoes

### Principios (3-5)

1. **Continuidade do Contexto** — O historico de conversas nao deve ser perdido ao reiniciar o bot
2. **Minima Intrusao** — A integracao nao deve afetar a logica existente do bot Discord
3. **Alinhamento de Dominio** — Schema de dados deve refletir o modelo do dominio (DiscordSession com thread_id, user_id, modo)
4. **Seguranca** — Credenciais de banco nunca devem ser hardcoded; sempre via variaveis de ambiente
5. **Idempotencia** — A solucao deve funcionar corretamente mesmo se a tabela do banco ja exista
6. **Camada Unica** — Persistencia deve ser gerida por um unico componente (SessionDAO), sem redundancia
7. **API Compliance** — Deve usar APENAS recursos validos da API do Agno

### Decision Drivers (Top 3)

1. **Custo de infraestrutura** — Supabase oferece tier gratuito adequado para o volume do bot
2. **Complexidade de implementacao** — Integracao deve levar menos de 2 horas para completar
3. **Confiabilidade de dados** — Historico de sessoes e critico para experiencia do usuario

### Opcoes Viaveis

#### Opcao A: PostgresDb do Agno (REJEITADA)

**Pros:**
- Nativa ao framework Agno (nenhuma dependencia adicional)
- Tabela de sessoes criada automaticamente (`agno_sessions` no schema `ai`)
- Suporte built-in para migracoes e schema

**Cons:**
- **Lock-in estrutural**: Schema com 7 colunas JSONB proprietarias
- Schema do `ai.agno_sessions` possui 17 colunas, mas o bot usa apenas 2 valores
- **CRITICO**: Cria dupla camada de persistencia quando combinado com SessionDAO

**Razao para rejeicao:** O Critic identificou que manter `PostgresDb` E `SessionDAO` simultaneamente cria redundancia de dados e inconsistencia.

#### Opcao B: psycopg2 direto + custom DAO (ESCOLHIDA)

**Pros:**
- Controle total sobre schema e queries
- Schema do dominio: `discord_sessions` com colunas semanticas
- Otimizacoes especificas possiveis (indexes, partial indexes)
- Independente de versoes do Agno
- Portabilidade real: SQLAlchemy permite trocar backend PostgreSQL
- Camada unica de persistencia (sem redundancia)

**Cons:**
- Requer escrita de DAO customizado (~100 LOC)
- Migracoes precisam ser gerenciadas manualmente
- Maior superficie de bugs (para ser mitigada com testes)

**Custo de Implementacao:**
- Linhas de codigo: ~120 LOC
- Tempo: ~2 horas

### Analise de Trade-offs

| Dimensao | Opcao A (Agno) | Opcao B (Custom) |
|----------|----------------|------------------|
| Velocidade | < 1h | ~2h |
| Manutenibilidade | Baixa (lock-in) | Alta (controle) |
| Custo Saida | Alto (ETL manual) | Baixo |
| Alinhamento Dominio | Baixo | Alto |
| Camada Unica | NAO (dupla com SessionDAO) | SIM |

**Decisao:** **Opcao B (psycopg2 + custom DAO)** — UNICA camada de persistencia

**Justificativa:**
1. O bot de estudos e um projeto de dominio especifico (Discord) com necessidades de evolucao
2. O controle de schema e valioso para adicionar features futuras (tags, favoritos, estatisticas)
3. A arquiteta do Architect identifica que delegar estrutura de dados a framework opinativo (Agno) e suboptimo para este caso de uso
4. O custo adicional de ~100 LOC (~1 hora) e compensado pela manutenibilidade e custo de saida reduzido
5. **CRITICO**: Evita dupla camada de persistencia que o Critic identificou como problema fatal

---

## Objetivos do Trabalho

1. Configurar backend PostgreSQL via Supabase para persistencia de sessoes
2. Criar DAO customizado com SQLAlchemy para gerenciar sessoes Discord
3. Modificar `create_agent()` para suportar reinicializacao de contexto
4. Modificar `bot.py` para salvar historico apos cada resposta
5. Atualizar configuracao e dependencias
6. Corrigir race condition em `get_or_create_session`
7. Recuperar historico e passar para Agent via API valida do Agno
8. Adicionar tratamento de erro quando DB falha
9. Implementar limpeza de sessoes antigas

---

## Guardrails

### Must Have (Obrigatorio)

- [ ] Historico de sessoes persiste entre reinicializacoes do bot
- [ ] Credenciais via variavel de ambiente (SUPABASE_DB_URL)
- [ ] DAO customizado com SQLAlchemy (UNICA camada de persistencia)
- [ ] Schema do dominio: `discord_sessions` com colunas semanticas
- [ ] Bot Discord continua funcionando sem regressoes
- [ ] 4 modos de operacao mantidos (Estudo, Professor, Simulado, Casual)
- [ ] Hook em `bot.py:_process_message()` salva historico apos `arun()`
- [ ] API do Agno respeitada (sem `agent.memory.messages`)
- [ ] NENHUM uso do PostgresDb do Agno
- [ ] Tratamento de erro quando DB falha (fallback memoria)
- [ ] Limpeza de sessoes antigas implementada

### Must NOT Have (Proibido)

- [ ] Nenhuma credencial hardcoded no codigo
- [ ] Nenhuma mudanca nos prompts/instrucoes base do agente
- [ ] Nenhuma alteracao na logica de filtragem guild/channel
- [ ] Nenhuma dependencia desnecessaria adicionada
- [ ] Nenhum uso do schema `ai.agno_sessions` do Agno
- [ ] Nenhuma dupla camada de persistencia (PostgresDb + SessionDAO)
- [ ] Nenhuma manipulacao de `agent.memory.messages` (API invalida)

---

## Fluxo de Trabalho

```mermaid
graph LR
    A[Adicionar SQLAlchemy] --> B[Criar modelo DiscordSession]
    B --> C[Criar DAO customizado SessionDAO]
    C --> D[Modificar create_agent]
    D --> E[Adicionar hook em bot.py]
    E --> F[Atualizar config.py]
    F --> G[Atualizar .env.example]
    G --> H[Testar persistencia]
```

---

## TODOs Detalhados

### Passo 1: Adicionar dependencias SQLAlchemy

**Arquivo:** `pyproject.toml`

**Acao:** Adicionar `sqlalchemy` e `psycopg[binary]` as dependencias do projeto.

**Rationale:** SQLAlchemy fornece ORM portavel. psycopg[binary] e o driver PostgreSQL (versao binary evita problemas de compilacao no macOS ARM).

**Alteracao:**
```toml
dependencies = [
    "agno>=1.0.0",
    "discord.py>=2.4.0",
    "requests>=2.32.0",
    "openai>=1.0.0",
    "sqlalchemy>=2.0.0",      # NOVO
    "psycopg[binary]>=3.2.0",  # NOVO
]
```

**Criterios de Aceitacao:**
- [ ] `uv sync` executa sem erros
- [ ] `sqlalchemy` e `psycopg` aparecem em `uv pip list`

---

### Passo 2: Criar modelo DiscordSession

**Arquivo NOVO:** `oraculo_bot/models.py`

**Acao:** Definir modelo SQLAlchemy para sessoes Discord com schema do dominio.

**Conteudo:**
```python
"""Modelos de dados do OraculoBOT."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, create_engine, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session


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
    """Cria as tabelas no banco de dados."""
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
```

**Criterios de Aceitacao:**
- [ ] Modelo define todas as colunas necessarias
- [ ] `thread_id` e chave primaria (ID unico do thread Discord)
- [ ] `user_id` tem indice para consultas por usuario
- [ ] `mode` permite os 4 modos de operacao
- [ ] `session_data` JSONB para flexibilidade futura

---

### Passo 3: Criar DAO customizado (thread-safe + tratamento de erro)

**Arquivo NOVO:** `oraculo_bot/db.py`

**Acao:** Implementar DAO (Data Access Object) para gerenciar sessoes.

**IMPORTANTE:** `get_or_create_session` DEVE ser thread-safe usando `INSERT ... ON CONFLICT`.
**CRITICO:** Adicionar tratamento de erro quando DB falha (fallback memoria).

**Conteudo:**
```python
"""Camada de acesso a dados do OraculoBOT."""

import logging
from typing import Optional

from sqlalchemy import create_engine, select, text
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
    def engine(self):
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
            from sqlalchemy import func
            from datetime import timedelta, timezone

            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

            with Session(self.engine) as session:
                stmt = select(DiscordSession).where(
                    DiscordSession.updated_at < cutoff_date
                )
                old_sessions = session.execute(stmt).scalars().all()

                count = len(old_sessions)
                for s in old_sessions:
                    session.delete(s)

                session.commit()
                logger.info(f"Removidas {count} sessoes antigas (> {days} dias)")
                return count
        except Exception as e:
            logger.error(f"Erro ao limpar sessoes antigas: {e}")
            return 0
```

**Criterios de Aceitacao:**
- [ ] DAO implementa CRUD basico para sessoes
- [ ] `enabled` retorna False quando SUPABASE_DB_URL nao configurada
- [ ] `get_or_create_session` e thread-safe (usa ON CONFLICT)
- [ ] Todas as operacoes DAO tem tratamento de erro (fallback memoria)
- [ ] `cleanup_old_sessions()` remove sessoes com mais de X dias
- [ ] NENHUM uso de PostgresDb do Agno

---

### Passo 4: Atualizar config.py

**Arquivo:** `oraculo_bot/config.py`

**Acao:** Adicionar constante `SUPABASE_DB_URL` com tratamento opcional.

**Alteracao:**
```python
# -- Banco de Dados ---------------------------------------------------------
SUPABASE_DB_URL: str | None = os.getenv("SUPABASE_DB_URL")
```

**Nota:** O valor e opcional (`None`) para permitir que o bot funcione sem persistencia durante desenvolvimento local.

**Criterios de Aceitacao:**
- [ ] `SUPABASE_DB_URL` pode ser undefined sem quebrar o bot
- [ ] Quando definida, a URL e uma string valida

---

### Passo 5: Modificar agent.py (CORRECAO CRITICA - API Agno)

**Arquivo:** `oraculo_bot/agent.py`

**Acao:** Integrar DAO customizado para salvar/carregar historico.

**IMPORTANTE:** NAO manipular `agent.memory.messages` (API invalida).
Usar `add_history_to_context=True` + `session_id` do Agno.

**Alteracoes:**

1. Adicionar imports:
```python
from agno.agent import Agent
from agno.models.deepseek import DeepSeek

from oraculo_bot.config import HISTORY_RUNS, MODEL_ID
from oraculo_bot.db import SessionDAO  # NOVO
from oraculo_bot.models import DiscordSession  # NOVO
```

2. Adicionar instancia global do DAO:
```python
# DAO para persistencia de sessoes (UNICA camada)
_session_dao = SessionDAO()
```

3. Adicionar funcoes de gerenciamento de sessao:
```python
def initialize_session(
    thread_id: str,
    user_id: str,
    mode: str = "estudo",
) -> DiscordSession:
    """Inicializa ou recupera uma sessao do banco.

    Args:
        thread_id: ID do thread Discord.
        user_id: ID do usuario Discord.
        mode: Modo de operacao (usado apenas na criacao).

    Returns:
        A sessao encontrada ou criada.
    """
    return _session_dao.get_or_create_session(
        thread_id=thread_id,
        user_id=user_id,
        mode=mode,
    )


def save_session_history(thread_id: str, messages: list) -> None:
    """Salva o historico da conversa no banco.

    Args:
        thread_id: ID do thread Discord.
        messages: Lista de mensagens da conversa (RunOutput.messages).
    """
    _session_dao.update_session_data(thread_id, {"history": messages})


def get_session_history(thread_id: str) -> list:
    """Recupera o historico de uma sessao.

    Args:
        thread_id: ID do thread Discord.

    Returns:
        Lista de mensagens da sessao ou lista vazia.
    """
    session = _session_dao.get_session(thread_id)
    if session:
        return session.session_data.get("history", [])
    return []


def cleanup_old_sessions(days: int = 30) -> int:
    """Remove sessoes antigas do banco.

    Args:
        days: Numero de dias para considerar uma sessao como antiga.

    Returns:
        Numero de sessoes removidas.
    """
    return _session_dao.cleanup_old_sessions(days)
```

**Manter `create_agent()` inalterado** - O Agno ja suporta multiplos `session_id` na mesma instancia:

```python
def create_agent() -> Agent:
    """Cria e retorna a instância do Agent Oráculo.

    Nota: O Agent e reutilizavel para multiplas sessoes via session_id.
    """
    return Agent(
        name="Oráculo",
        model=DeepSeek(id=MODEL_ID),
        instructions=SYSTEM_INSTRUCTIONS,
        add_history_to_context=True,  # Agno gerencia historico automaticamente
        num_history_runs=HISTORY_RUNS,
        add_datetime_to_context=True,
        markdown=True,
    )
```

**Criterios de Aceitacao:**
- [ ] `create_agent()` mantem assinatura original (sem quebrar codigo existente)
- [ ] NENHUM uso de `agent.memory.messages` (API invalida)
- [ ] `initialize_session()` carrega sessao existente quando disponivel
- [ ] `save_session_history()` persiste mensagens no banco
- [ ] `get_session_history()` recupera historico salvo
- [ ] `cleanup_old_sessions()` remove sessoes antigas
- [ ] NENHUM uso de PostgresDb do Agno

---

### Passo 6: Modificar bot.py (CORRECAO CRITICA - Hook para salvar)

**Arquivo:** `oraculo_bot/bot.py`

**Acao:** Adicionar hook para salvar historico apos `arun()`.

**ALTERACOES CRITICAS:**
1. Importar funcoes de persistencia
2. Carregar historico antes de chamar `arun()`
3. Salvar historico apos `arun()` completar

**Alteracoes:**

1. Adicionar imports:
```python
from oraculo_bot.config import (
    DISCORD_BOT_TOKEN,
    ERROR_MESSAGE,
    MAX_MESSAGE_LENGTH,
    TARGET_CHANNEL_ID,
    TARGET_GUILD_ID,
    THREAD_NAME_PREFIX,
)
from oraculo_bot.agent import initialize_session, save_session_history, get_session_history  # NOVO
from oraculo_bot.views import ConfirmationView
```

2. Modificar `_process_message()` para adicionar hooks de persistencia:

```python
async def _process_message(self, message: discord.Message) -> None:
    """Pipeline completo: persistencia -> midia -> thread -> agent -> salvar -> resposta."""
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
        log_info(f"Canal nao suportado: {type(message.channel)}")
        return

    # Inicializar/recuperar sessao do banco
    thread_id_str = str(thread.id)
    user_id_str = str(user_id)

    # TODO: Detectar modo baseado no conteudo da mensagem
    # Por enquanto, usa modo padrao "estudo"
    discord_session = initialize_session(
        thread_id=thread_id_str,
        user_id=user_id_str,
        mode="estudo",
    )

    # Carregar historico existente (se houver)
    # Nota: O Agno usa session_id para tracking, mas precisamos
    # garantir que o historico carregado seja usado no contexto
    session_history = get_session_history(thread_id_str)

    mention = f"<@{user_id}>"
    context = dedent(f"""
        Discord username: {user_name}
        Discord userid: {user_id}
        Discord url: {message.jump_url}
        Session mode: {discord_session.mode}
        Previous messages: {len(session_history)}
    """)
    media_kwargs = self._build_media_kwargs(img, vid, aud, fil)

    async with thread.typing():
        runner = self.agent or self.team
        runner.additional_context = context  # type: ignore[union-attr]

        response = await runner.arun(  # type: ignore[union-attr]
            input=message.content,
            user_id=user_id,
            session_id=thread_id_str,  # Agno usa isso para tracking
            **media_kwargs,
        )

        if response.status == "ERROR":
            log_error(response.content)
            response.content = ERROR_MESSAGE

        # CRITICO: Salvar historico apos cada resposta
        if response.messages:
            save_session_history(thread_id_str, response.messages)

        await self._handle_response(response, thread, mention)
```

**Criterios de Aceitacao:**
- [ ] `initialize_session()` e chamado antes de processar mensagem
- [ ] `get_session_history()` recupera historico anterior
- [ ] `save_session_history()` e chamado apos `arun()` completar
- [ ] Historico e salvo mesmo quando response.status == "ERROR"
- [ ] NENHUM uso de `agent.memory.messages`

---

### Passo 7: Adicionar inicializacao do DAO em __main__.py

**Arquivo:** `oraculo_bot/__main__.py`

**Acao:** Inicializar o DAO ao iniciar o bot.

**Alteracao:**
```python
"""Entrypoint: python -m oraculo_bot."""

from oraculo_bot.agent import create_agent, cleanup_old_sessions
from oraculo_bot.bot import OracleDiscordBot


def main() -> None:
    # Inicializar DAO e criar tabelas se necessario
    from oraculo_bot.db import SessionDAO
    dao = SessionDAO()
    dao.init_db()

    # Limpar sessoes antigas (opcional - a cada 30 dias)
    cleanup_old_sessions(days=30)

    agent = create_agent()
    bot = OracleDiscordBot(agent=agent)
    bot.serve()


if __name__ == "__main__":
    main()
```

**Criterios de Aceitacao:**
- [ ] `dao.init_db()` e chamado ao iniciar o bot
- [ ] `cleanup_old_sessions()` e chamado na inicializacao
- [ ] Bot funciona sem SUPABASE_DB_URL (fallback memoria)

---

### Passo 8: Atualizar .env.example

**Arquivo:** `.env.example`

**Acao:** Adicionar exemplo de configuracao Supabase.

**Alteracao:**
```bash
# Discord
DISCORD_BOT_TOKEN=

# DeepSeek
DEEPSEEK_API_KEY=

# Supabase PostgreSQL (opcional — para persistencia de sessoes)
# Formato: postgresql+psycopg://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
SUPABASE_DB_URL=

# Bot config (optional — defaults in config.py)
# TARGET_GUILD_ID=1283924742851661844
# TARGET_CHANNEL_ID=1486301006659715143
# MODEL_ID=deepseek-chat
# HISTORY_RUNS=5
```

**Criterios de Aceitacao:**
- [ ] Comentario explica formato da URL
- [ ] Valor vazio por padrao (opt-in)

---

### Passo 9: Estrategia de Detecção de Modo

**Arquivo NOVO:** `oraculo_bot/mode_detector.py` (opcional)

**Acao:** Implementar deteccao automatica de modo baseado no conteudo da mensagem.

**Conteudo:**
```python
"""Detecção automatica de modo baseada no conteudo da mensagem."""

from typing import Optional

import re


def detect_mode(message_content: str, thread_history: list) -> str:
    """Detecta o modo de operacao baseado no conteudo.

    Args:
        message_content: Conteudo da mensagem atual.
        thread_history: Historico de mensagens do thread.

    Returns:
        Modo detectado: 'estudo', 'professor', 'simulado', ou 'casual'.
    """
    content_lower = message_content.lower()

    # Palavras-chave para cada modo
    estudo_keywords = [
        'edital', 'banca', 'legislacao', 'jurisprudencia', 'sumula',
        'artigo', 'inciso', 'alinea', 'doutrina', 'posicao da banca',
        'estudar', 'materia', 'conteudo', 'cronograma'
    ]

    professor_keywords = [
        'explica', 'entendi', 'duvida', 'conceito', 'oque eh',
        'comofunciona', 'exemplo', 'analogia', 'ensina'
    ]

    simulado_keywords = [
        'questao', 'prova', 'exercicio', 'alternativa', 'certo',
        'errado', 'gabarito', 'comentario', 'resolve', 'simulado'
    ]

    casual_keywords = [
        'oi', 'ola', 'bom dia', 'boa tarde', 'boa noite', 'tudo bem',
        'obrigado', 'valeu', 'desabafar', 'cansado', 'motivacao'
    ]

    # Contar matches por modo
    estudo_count = sum(1 for kw in estudo_keywords if kw in content_lower)
    professor_count = sum(1 for kw in professor_keywords if kw in content_lower)
    simulado_count = sum(1 for kw in simulado_keywords if kw in content_lower)
    casual_count = sum(1 for kw in casual_keywords if kw in content_lower)

    # Detectar questoes (padrao de prova)
    questao_pattern = r'^(c|e|certo|errado|analtica:?\s*\d+|comentado:?\s*\d+)'
    if re.search(questao_pattern, content_lower, re.MULTILINE):
        simulado_count += 3  # Bonus alto para questoes

    # Escolher modo com maior score
    scores = {
        'estudo': estudo_count,
        'professor': professor_count,
        'simulado': simulado_count,
        'casual': casual_count,
    }

    max_score = max(scores.values())
    if max_score == 0:
        return 'estudo'  # Default

    for mode, score in scores.items():
        if score == max_score:
            return mode

    return 'estudo'  # Default (nunca deve chegar aqui)
```

**Uso em `bot.py`:**
```python
from oraculo_bot.mode_detector import detect_mode

# Em _process_message():
mode = detect_mode(message.content, [])
discord_session = initialize_session(
    thread_id=thread_id_str,
    user_id=user_id_str,
    mode=mode,
)
```

**Criterios de Aceitacao:**
- [ ] `detect_mode()` analisa conteudo da mensagem
- [ ] Palavras-chave cobrem os 4 modos
- [ ] Pattern regex detecta questoes de prova
- [ ] Retorno padrao e 'estudo' quando nenhum modo detectado

---

### Passo 10: Teste de Persistencia

**Procedimento Manual:**

1. Criar projeto no Supabase e obter URL de conexao
2. Configurar `.env` com SUPABASE_DB_URL
3. Iniciar o bot: `oraculo-bot`
4. Enviar uma mensagem no Discord e anotar o thread ID
5. Verificar no Supabase que a tabela `discord_sessions` contem registros:
   ```sql
   SELECT * FROM discord_sessions;
   ```
6. Parar o bot (`Ctrl+C`)
7. Reiniciar o bot
8. Enviar nova mensagem no mesmo thread
9. Verificar se o bot mantem contexto da conversa anterior
10. Verificar se as instrucoes do modo estao sendo aplicadas

**Criterios de Aceitacao:**
- [ ] Tabela `discord_sessions` criada automaticamente pelo SQLAlchemy
- [ ] Sessao persiste apos reinicio do bot
- [ ] Historico de mensagens e recuperado corretamente
- [ ] Modos de operacao (Estudo/Professor/Simulado/Casual) funcionam
- [ ] Colunas `thread_id`, `user_id`, `mode` sao semanticas e uteis
- [ ] Nenhuma tabela `ai.agno_sessions` e criada (confirma que PostgresDb nao e usado)
- [ ] Bot funciona quando DB falha (fallback memoria)

**Query SQL para verificacao:**
```sql
-- Verificar sessoes por usuario
SELECT user_id, mode, COUNT(*) as sessions, MAX(updated_at) as last_activity
FROM discord_sessions
GROUP BY user_id, mode
ORDER BY last_activity DESC;

-- Verificar dados de uma sessao especifica
SELECT thread_id, user_id, mode, session_data, created_at, updated_at
FROM discord_sessions
WHERE thread_id = '1234567890';

-- Confirmar que tabela agno_sessions NAO existe
SELECT table_name FROM information_schema.tables
WHERE table_name = 'agno_sessions';
-- Resultado esperado: 0 rows
```

---

## ADR (Architecture Decision Record)

### Decisao
Usar APENAS DAO customizado com SQLAlchemy + backend Supabase PostgreSQL para persistencia de sessoes do OraculoBOT. PostgresDb do Agno foi completamente removido da solucao.

### Drivers (Contexto)
- Bot atual perde historico ao reiniciar (armazenamento em memoria)
- Necessidade de continuidade de contexto para experiencia do usuario
- Orcamento limitado (preferencia por solucoes gratuitas/free-tier)
- Projeto de dominio especifico (Discord) com necessidades de evolucao futura
- **CRITICO**: Critic identificou dupla camada de persistencia (PostgresDb + SessionDAO) como problema fatal
- **CRITICO**: Manipulacao de `agent.memory.messages` e invalida na API do Agno

### Alternativas Consideradas

1. **SQLAlchemy + Custom DAO** (ESCOLHIDA)
   - Custo: Free tier adequado
   - Complexidade: Media (~120 LOC)
   - Manutenibilidade: Alta (controle total)
   - Alinhamento dominio: Alto (schema semantico)
   - Custo saida: Baixo (portabilidade real)
   - **Camada unica**: SIM
   - **API Compliance**: SIM (usa recursos validos do Agno)

2. **PostgresDb Agno + Supabase** (REJEITADA)
   - Custo: Free tier adequado
   - Complexidade: Baixa (~20 LOC)
   - Manutenibilidade: Baixa (lock-in estrutural)
   - Alinhamento dominio: Baixo (schema generico)
   - Custo saida: Alto (ETL manual necessario)
   - **CRITICO**: Criaria dupla camada de persistencia com SessionDAO
   - Schema `ai.agno_sessions` com 7 colunas JSONB proprietarias

3. **Adapter Customizado** (descartada)
   - Custo: Free tier adequado
   - Complexidade: Media (~60 LOC)
   - Manutenibilidade: Media (herda lock-in parcial)
   - Complicacao adicional sem beneficio claro vs Opcao B

### Por Que APENAS SQLAlchemy + Custom DAO
- Controle de schema valioso para projeto em evolucao
- Alinhamento com principio "Alinhamento de Dominio"
- Alinhamento com principio "Camada Unica"
- Portabilidade real via SQLAlchemy
- Evita lock-in estrutural do schema Agno
- Elimina redundancia de dados
- **CRITICO**: Usa apenas API valida do Agno (`add_history_to_context=True` + `session_id`)

### Consequencias

**Positivas:**
- Sessoes persistem entre reinicializacoes
- Schema semanticamente alinhado com dominio Discord
- Dashboard Supabase para inspecao manual
- Evolucao futura facilitada
- Custo de saida reduzido
- Camada unica de persistencia
- API compliance com Agno

**Negativas:**
- Requer manutencao de DAO customizado
- Migracoes manuais (Alembic disponivel se necessario)
- Implementacao inicial ~1 hora a mais que Opcao A

### Follow-ups
- Monitorar uso de espaco no Supabase apos 30 dias
- Considerar Alembic para migrations se schema evoluir
- Avaliar indexes adicionais baseado em queries frequentes
- Implementar deteccao automatica de modo (Passo 9 - opcional)

---

## Plano de Testes

### Unitario

| Caso | Teste | Resultado Esperado |
|------|-------|-------------------|
| DAO sem DB URL | Criar SessionDAO sem URL | `enabled` retorna False |
| DAO get_session | Buscar sessao inexistente | Retorna None |
| DAO create_session | Criar nova sessao | Sessao criada com ID gerado |
| DAO update_session | Atualizar sessao existente | Dados atualizados |
| DAO get_or_create_thread_safe | Duas chamadas simultaneas | Apenas uma sessao criada |
| DAO tratamento erro | Simular falha de conexao | Fallback para memoria |
| save_session_history | Salvar lista de mensagens | Dados persistidos no banco |
| get_session_history | Recuperar historico salvo | Retorna lista de mensagens |
| cleanup_old_sessions | Sessoes com 40 dias | Removidas, retorna count |
| detect_mode estudio | Mensagem com "edital" | Retorna "estudo" |
| detect_mode simulado | Mensagem com questao | Retorna "simulado" |

### Integracao

| Caso | Passos | Resultado Esperado |
|------|--------|-------------------|
| Bot sem DB URL | Iniciar sem SUPABASE_DB_URL | Bot funciona em modo memoria |
| Bot com DB URL valida | Iniciar com SUPABASE_DB_URL valida | Tabela criada, bot funciona |
| Persistencia de sessao | Enviar msg, reiniciar, enviar no mesmo thread | Contexto mantido |
| Múltiplos threads | 3 usuarios simultaneos | Cada sessao independente |
| Hook de salvamento | Enviar mensagem | Historico salvo apos arun() |
| Detecção de falha DB | Desconectar DB durante operacao | Bot continua (fallback memoria) |

### E2E

1. Criar projeto Supabase teste
2. Configurar `.env` com URL do projeto teste
3. Executar cenario de persistencia (Passo 10)
4. Verificar dados no dashboard Supabase
5. Testar todos os 4 modos de operacao
6. Confirmar que tabela `agno_sessions` NAO foi criada
7. Testar fallback quando DB falha

---

## Riscos e Mitigacoes

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|---------------|---------|-----------|
| Supabase downtime | Baixa | Alto | Modo memoria automatico |
| Excesso de requisicoes | Baixa | Medio | Supabase free tier: 500MB |
| Bug no DAO customizado | Medio | Alto | Testes unitarios + integracao |
| Schema incompativel | Muito Baixa | Medio | SQLAlchemy cria tabela automaticamente |
| Lock-in PostgreSQL | Baixa | Alto | SQLAlchemy permite trocar backend |
| Evolucao de schema | Media | Baixo | Alembic disponivel |
| Race condition get_or_create | Baixa | Alto | INSERT ... ON CONFLICT |
| Falha de conexao | Media | Medio | Fallback memoria implementado |

---

## Critérios de Sucesso

1. [ ] Todas as alteracoes implementadas conforme especificado
2. [ ] `uv sync` executa sem erros
3. [ ] Bot inicia com e sem `SUPABASE_DB_URL`
4. [ ] Historico persiste entre reinicializacoes
5. [ ] Dashboard Supabase mostra sessoes em tabela `discord_sessions`
6. [ ] Nenhuma regressao nos modos de operacao
7. [ ] Schema `discord_sessions` possui colunas semanticas
8. [ ] Hook em `bot.py` salva historico apos `arun()`
9. [ ] NENHUM uso de `agent.memory.messages`
10. [ ] NENHUMA tabela `ai.agno_sessions` criada
11. [ ] Tratamento de erro quando DB falha
12. [ ] Limpeza de sessoes antigas funciona

---

## Verificacao Final

```bash
# 1. Verificar dependencias instaladas
uv pip list | grep -E "sqlalchemy|psycopg"

# 2. Verificar import dos modulos
python -c "from oraculo_bot.db import SessionDAO; print('DAO OK')"
python -c "from oraculo_bot.models import DiscordSession; print('Models OK')"
python -c "from oraculo_bot.agent import initialize_session, save_session_history; print('Agent OK')"

# 3. Verificar config carrega sem erro
python -c "from oraculo_bot.config import SUPABASE_DB_URL; print(f'SUPABASE_DB_URL={SUPABASE_DB_URL}')"

# 4. Verificar que PostgresDb do Agno nao e usado
grep -r "PostgresDb" oraculo_bot/ || echo "Nenhuma referencia a PostgresDb encontrada (OK)"

# 5. Verificar que agent.memory.messages nao e usado
grep -r "agent.memory" oraculo_bot/ || echo "Nenhuma referencia a agent.memory encontrada (OK)"

# 6. Iniciar bot (dry run)
oraculo-bot --help 2>/dev/null || echo "Bot executavel"
```

---

## Anexos

### Formato de URL Supabase

```
postgresql+psycopg://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

### Schema discord_sessions (SQLAlchemy)

```sql
CREATE TABLE discord_sessions (
    thread_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    mode VARCHAR(32) NOT NULL DEFAULT 'estudo',
    session_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_discord_sessions_user_id ON discord_sessions(user_id);
```

### Comparativo de Schema

| Aspecto | Agno (`ai.agno_sessions`) | Custom (`discord_sessions`) |
|---------|--------------------------|-----------------------------|
| Tabela | `agno_sessions` | `discord_sessions` |
| Schema | `ai` | `public` |
| Colunas | 17 colunas | 6 colunas |
| Colunas JSONB | 7 proprietarias | 1 generica |
| Alinhamento | Generico | Especifico (Discord) |
| Portabilidade | Baixa | Alta |
| Camada de persistencia | Dupla | Unica |

---

## Historico de Revisoes

### Revisao 3 (2025-03-25) - ITERAÇÃO 3 (CORRECOES CRITICAS)
- **CORRECAO CRITICA #1**: Removida manipulacao invalida de `agent.memory.messages`
- **CORRECAO CRITICA #2**: Adicionado hook em `bot.py` para salvar historico apos `arun()`
- **CORRECAO CRITICA #3**: Removido padrao `agent_factory` (reutilizando instancia unica do Agent)
- Usando recursos nativos do Agno: `add_history_to_context=True` + `session_id`
- Adicionado tratamento de erro quando DB falha (fallback memoria)
- Adicionado `cleanup_old_sessions()` para limpeza de sessoes antigas
- Adicionado `mode_detector.py` opcional para deteccao automatica de modo
- Mantida assinatura original de `create_agent()` (sem quebrar codigo existente)
- Adicionadas funcoes: `initialize_session()`, `save_session_history()`, `get_session_history()`
- Atualizados criterios de aceite para verificar API compliance

### Revisao 2 (2025-03-25)
- Incorporou feedback completo do Architect e Critic
- Removido completamente PostgresDb do Agno
- SessionDAO agora e a UNICA camada de persistencia
- Modificada assinatura de `create_agent()` para receber thread_id, user_id, mode
- Implementada correcao thread-safe em `get_or_create_session`

### Revisao 1 (2025-03-25)
- Versao inicial rejeitada pelo Critic
