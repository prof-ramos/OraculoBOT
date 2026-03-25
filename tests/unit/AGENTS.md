<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-25 -->

# unit

## Purpose
Testes unitários dos módulos do OraculoBOT com alta cobertura.

## Key Files
| File | Description |
|------|-------------|
| `test_agent.py` | Testes do agente IA |
| `test_bot.py` | Testes do bot Discord |
| `test_config.py` | Testes de configuração |
| `test_db.py` | Testes do SessionDAO |
| `test_models.py` | Testes dos modelos |
| `test_rag_retriever.py` | Testes do RAG |
| `test_views.py` | Testes das views Discord |

## For AI Agents

### Testing Requirements
- 152 testes atualmente passando
- Usar fixtures de conftest.py global

### Common Patterns
- pytest.mark.asyncio para testes assíncronos
- mocker.patch para isolar dependências