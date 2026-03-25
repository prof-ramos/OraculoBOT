<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-25 -->

# oraculo_bot

## Purpose
Módulo principal do bot Discord com IA especializada em concursos públicos.

## Key Files
| File | Description |
|------|-------------|
| `__main__.py` | Entry point do bot |
| `agent.py` | Criação e configuração do Agent Oráculo |
| `bot.py` | OracleDiscordBot - lógica principal do Discord |
| `config.py` | Variáveis de ambiente e configurações |
| `db.py` | SessionDAO - persistência de sessões |
| `models.py` | DiscordSession - modelo de dados |
| `rag.py` | Interface RAG para legislação |
| `rag_retriever.py` | RAGRetriever - busca vetorial |
| `views.py` | ConfirmationView - UI Discord (HITL) |

## For AI Agents

### Working In This Directory
- Bot usa discord.py com intents.all()
- Agent usa DeepSeek via agno
- RAG opcional via pgvector

### Testing Requirements
- Cada módulo tem testes em tests/unit/
- Mock para Discord client

### Common Patterns
- from __future__ import annotations
- Log com agno.utils.log
- Async/await para Discord

## Dependencies

### Internal
- Usa config.py em todos os módulos

### External
- discord.py - Discord API
- agno - Agent framework
- sqlalchemy - Database ORM