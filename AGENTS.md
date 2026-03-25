<!-- Generated: 2026-03-25T16:09:00Z -->

# oraculobot

## Purpose
Bot Discord de estudos para concursos públicos brasileiros, construído com Agno + discord.py que responde automaticamente no canal configurado com 4 modos adaptativos, suporte a mídia, e RAG integrado.

## Key Files
| File | Description |
|------|-------------|
| `pyproject.toml` | Configuração de projeto, dependências e scripts Python |
| `README.md` | Documentação completa de setup e configuração do bot |
| `.env.example` | Template de variáveis de ambiente para Discord, DeepSeek, Gemini e Supabase |

## Subdirectories
| Directory | Purpose |
|-----------|---------|
| `docs/` | Documentação (see `docs/AGENTS.md`) |
| `oraculo_bot/` | Código principal (see `oraculo_bot/AGENTS.md`) |
| `scripts/` | Scripts utilitários (see `scripts/AGENTS.md`) |
| `tests/` | Suíte de testes (see `tests/AGENTS.md`) |

## For AI Agents

### Working In This Directory
- Usar uv para gerenciar dependências
- Python 3.11+ requerido
- Seguir PEP 8

### Testing Requirements
- Rodar `uv run pytest tests/unit/` antes de commits
- Manter coverage >60%

### Common Patterns
- Type hints obrigatórios
- Async/await para Discord

## Dependencies

### External
- discord.py - Discord bot framework
- agno - AI agent framework
- deepseek - LLM
- psycopg3/pgvector - PostgreSQL vetorial
