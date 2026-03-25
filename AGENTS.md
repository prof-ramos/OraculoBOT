<!-- Generated: 2026-03-25 | Updated: 2026-03-25 -->

# OraculoBOT

## Purpose

Bot Discord de estudos para concursos públicos brasileiros, construído com Agno (framework de agentes AI) e discord.py. O bot responde automaticamente em um canal configurado, cria threads por conversa com histórico preservado, e oferece 4 modos adaptativos: Estudo, Professor, Simulado e Casual.

## Key Files

| File | Description |
|------|-------------|
| `pyproject.toml` | Manifesto do projeto com dependências (agno, discord.py, openai) e configurações de build |
| `README.md` | Documentação do projeto: features, requisitos, setup e configuração |
| `.env.example` | Template de variáveis de ambiente necessárias (DISCORD_BOT_TOKEN, DEEPSEEK_API_KEY, etc) |
| `.gitignore` | Arquivos ignorados pelo git |
| `__init__.py` | Inicialização do pacote com versionamento |
| `__main__.py` | Entrypoint para execução via `python -m oraculo_bot` |
| `config.py` | Configuração centralizada via variáveis de ambiente (tokens, IDs, modelo, limites) |
| `agent.py` | Definição do Agent Agno com instruções do sistema (4 modos de operação) |
| `bot.py` | Core do bot: OracleDiscordBot (filtro guild/channel, threading, mídia, HITL) |
| `views.py` | Componentes de UI Discord (botões de confirmação para Human-in-the-Loop) |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `.omc/` | Estado do oh-my-claudecode (gerenciado automaticamente, não modificar) |

## For AI Agents

### Working In This Directory

- **Python**: Requer Python 3.11+, usar `uv` como gerenciador de pacotes
- **Execução**: `uv run python -m oraculo_bot`
- **Dependências**: Sempre execute `uv sync` antes de modificar código
- **Linting**: Configurado com Ruff (target: py311, line-length: 100)

### Testing Requirements

- Testar manualmente no Discord após alterações em `bot.py` ou `agent.py`
- Verificar se variáveis de ambiente estão configuradas (`.env`)

### Common Patterns

- **Imports**: Use `from __future__ import annotations` para type hints
- **Logging**: Use `agno.utils.log.log_info()` e `log_error()`
- **Config**: Valide env vars via `_require_env()` em `config.py`
- **Markdown**: Bot usa formatação Discord-compatible (`**negrito**`, `*itálico*`, ```código```)

## Dependencies

### External

- **agno>=1.0.0** - Framework de agentes AI (Agent, Team, RunOutput, media types)
- **discord.py>=2.4.0** - Lib oficial do Discord (Client, Intents, ui.View)
- **openai>=1.0.0** - Cliente OpenAI (base para DeepSeek)
- **requests>=2.32.0** - HTTP client para download de mídia

### Architecture

```
__main__.py → create_agent() + OracleDiscordBot() → serve()
                ↓                    ↓
            Agno Agent         Discord Client
            (instructions)     (events loop)
```

### Key Concepts

- **Filtro guild/channel**: Bot responde apenas em `TARGET_GUILD_ID`/`TARGET_CHANNEL_ID`
- **Threads por conversa**: Cada mensagem cria/usa uma thread com prefixo "💬 {username}"
- **HITL (Human-in-the-Loop)**: Tools que requerem confirmação mostram botões via `ConfirmationView`
- **Suporte a mídia**: Imagens (URL), vídeos/áudio (bytes), documentos (bytes)
- **Split de mensagens**: Textos >1500 chars são divididos em batches "[1/N] ..."

### Environment Variables

| Variável | Obrigatório | Default |
|----------|-------------|---------|
| `DISCORD_BOT_TOKEN` | ✅ | - |
| `DEEPSEEK_API_KEY` | ✅ | - |
| `TARGET_GUILD_ID` | ❌ | 1283924742851661844 |
| `TARGET_CHANNEL_ID` | ❌ | 1486301006659715143 |
| `MODEL_ID` | ❌ | deepseek-chat |
| `HISTORY_RUNS` | ❌ | 5 |

<!-- MANUAL: Notas manuais podem ser adicionadas abaixo desta linha -->
