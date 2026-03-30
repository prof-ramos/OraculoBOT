# 🔮 Oráculo Bot

Bot Discord de estudos para concursos públicos brasileiros, construído com [Agno](https://docs.agno.com) + [discord.py](https://discordpy.readthedocs.io/).

## Features

- Responde automaticamente no canal configurado (sem necessidade de menção)
- Cria threads por conversa com histórico preservado
- Menciona o autor (`@user`) em cada resposta
- 4 modos adaptativos: **Estudo**, **Professor**, **Simulado** e **Casual**
- Suporte a mídia: imagens, vídeos, áudio e documentos
- Split automático de mensagens longas (>1500 chars)
- Human-in-the-loop com botões de confirmação para tools
- Typing indicator durante processamento
- Integração com RAG jurídico no schema `juridico` do Supabase self-hosted

## Requisitos

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (gerenciador de pacotes)

## Setup

### 1. Clonar e instalar dependências

```bash
git clone <repo-url> && cd oraculo-bot
uv sync
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
# Edite .env com seus tokens
```

### 3. Configurar bot no Discord Developer Portal

1. Criar aplicação em [discord.com/developers](https://discord.com/developers/applications)
2. Em **Bot**, ativar:
   - `MESSAGE CONTENT INTENT`
   - `SERVER MEMBERS INTENT`
   - `PRESENCE INTENT`
3. Copiar o token para `.env`
4. Gerar link de convite em **OAuth2 > URL Generator**:
   - Scopes: `bot`
   - Permissions: `Send Messages`, `Create Public Threads`, `Send Messages in Threads`, `Read Message History`, `Attach Files`

### 4. Executar

```bash
uv run python -m oraculo_bot
```

## RAG Jurídico

O bot está preparado para consultar o RAG jurídico no schema `juridico` do Supabase self-hosted.

### Documentação do pipeline de ingestão do Lote 1

Se você vai implementar, revisar ou continuar o pipeline de ingestão do corpus jurídico, comece por:

- `docs/RAG_LOTE1/README.md`
- `docs/RAG_LOTE1/PASSO_2_CLASSIFICACAO_OPERACIONAL.md`
- `docs/RAG_LOTE1/PASSO_3_ESTRATEGIA_INGESTAO.md`
- `docs/RAG_LOTE1/PASSO_4_PLANO_TECNICO_EXECUTAVEL.md`
- `docs/RAG_LOTE1/PASSO_5_ESPECIFICACAO_IMPLEMENTACAO.md`

Esses arquivos definem:
- taxonomia e metadados
- ordem oficial de ingestão
- pipeline técnico
- schema lógico e pseudocódigo
- critérios de teste, quarentena e rollback

Regra prática: não implemente a ingestão “no improviso”. Comece por `eleitoral` e siga a ordem oficial.

Pontos esperados no banco:
- `juridico.documents`
- `juridico.chunks`
- `juridico.content_links`
- `juridico.match_chunks(...)`
- `juridico.match_chunks_hybrid(...)`
- coluna `juridico.chunks.search_text` para busca full-text em português
- índice GIN sobre `search_text`
- trigger para manter `search_text` atualizado
- extensão `unaccent` habilitada

A conexão é feita via `SUPABASE_DB_URL`.
O fluxo principal de recuperação agora pode combinar busca vetorial + full-text search em português.

## Configuração

Edite `src/oraculo_bot/config.py` para alterar:

| Variável | Descrição |
|----------|-----------|
| `DISCORD_BOT_TOKEN` | Token do bot Discord |
| `OPENAI_API_KEY` | Chave da API OpenAI |
| `TARGET_GUILD_ID` | ID do servidor Discord |
| `TARGET_CHANNEL_ID` | ID do canal de escuta |
| `MODEL_ID` | Modelo LLM (default: `gpt-4.1`) |
| `HISTORY_RUNS` | Quantidade de mensagens no histórico (default: `5`) |

## Estrutura

```
oraculo-bot/
├── src/oraculo_bot/
│   ├── __init__.py
│   ├── __main__.py        # Entrypoint
│   ├── config.py           # Configuração via env vars
│   ├── agent.py            # Definição do Agent + instructions
│   ├── bot.py              # OracleDiscordBot (core)
│   └── views.py            # UI components (HITL buttons)
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

## Licença

MIT
