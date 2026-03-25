<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-25 -->

# tests

## Purpose
Suíte de testes do OraculoBOT com foco em cobertura de módulos críticos.

## Key Files
| File | Description |
|------|-------------|
| `conftest.py` | Fixtures compartilhadas (Discord, RAG, env) |

## Subdirectories
| Directory | Purpose |
|-----------|---------|
| `unit/` | Testes unitários (see `unit/AGENTS.md`) |
| `e2e/` | Testes E2E/fixtures (see `e2e/AGENTS.md`) |

## For AI Agents

### Working In This Directory
- Usar pytest-mock, pytest-asyncio
- Fixtures usam spec=discord.* para isinstance()

### Testing Requirements
- Rodar `uv run pytest tests/unit/` antes de commits
- Target coverage: 70%+

### Common Patterns
- mock_env_vars autouse para variáveis de ambiente
- AsyncMock para métodos Discord
- MagicMock com spec para isinstance checks