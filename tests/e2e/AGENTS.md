<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-25 -->

# e2e

## Purpose
Infraestrutura E2E com fixtures especializadas e scripts de teste manual.

## Key Files
| File | Description |
|------|-------------|
| `conftest.py` | 17 fixtures E2E (bot, messages, threads, responses) |
| `README.md` | Explicação sobre testes automatizados removidos |

## For AI Agents

### Testing Requirements
- Testes E2E automatizados removidos (complexidade Discord mocks)
- Usar scripts/test_e2e_manual.py para testes manuais

### Common Patterns
- Mocks Discord com spec=discord.* para isinstance()
- AsyncMock para métodos assíncronos