# OraculoBOT - Claude Configuration

## Stack

**Backend:**
- Python 3.14.3
- Discord.py (async Discord bot)
- Agno Agent framework
- Supabase (PostgreSQL + pgvector)
- OpenAI API (embeddings)

**Frontend:**
- None (CLI Discord bot)

**Infrastructure:**
- Supabase Cloud (database)
- GitHub (code hosting)

**Testing:**
- pytest
- pytest-mock
- pytest-asyncio

---

## Estado Atual

**Última sessão (2026-03-26):**

Refatoração arquitetural completada via RALPLAN-DR consensus:

1. **Fix de Segurança** (commit d838292)
   - Corrigido SQL injection em `rag_retriever.py:92-95`
   - Substituído f-string por `psycopg.sql.Identifier()`
   - 31/31 testes passing

2. **Factory Pattern** (commit 7d9c914)
   - Adicionado `create_retriever(db_url=None)` em `rag.py`
   - Corrigida violação de DIP em `rag.py:16`
   - 3 novos testes unitários
   - 145/145 testes passing (0 regressions)

**Workflow RALPLAN-DR:**
- Iterações: 2 (Planner → Architect → Critic)
- Escopo reduzido: 7 fases → 2 fases (71% reduction)
- Consenso alcançado: APPROVED
- Implementação: via Team (parallel execution)

**Evidence Triggers (Phase 2 - Documentação):**
- Telegram implementation starts
- DB connection exhaustion observed
- Test suite requires explicit injection
- RAG fallback path requires testing

---

## Histórico de Decisões

**2026-03-26: Factory Pattern para RAG Retriever**
- Decisão: Adicionar factory function em vez de DI container completo
- Justificativa: Minimal viable refactor, evita over-engineering (YAGNI)
- Tradeoff: Mantém global `_rag_retriever` para compatibilidade, mas adiciona factory para DI
- Consequências: DIP corrigido, testabilidade melhorada, sem breaking changes
- Link: Commit 7d9c914

**2026-03-26: SQL Injection Fix**
- Decisão: Usar `psycopg.sql.Identifier()` em vez de sanitização manual
- Justificativa: Segurança crítica, proteção contra SQL injection em filtros de metadados
- Referência: `rag_retriever.py:92-95`
- Link: Commit d838292

**2026-03-26: Melhorias de Estilo Python**
- Decisão: Adicionar `from __future__ import annotations` em arquivos core
- Justificativa: PEP 563, melhor suporte a type hints, compatibilidade com mypy
- Arquivos modificados: agent.py, db.py, rag.py, rag_retriever.py, views.py
- Link: Commit a910867
