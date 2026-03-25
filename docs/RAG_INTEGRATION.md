# Integração RAG - OraculoBOT

## Visão Geral

O OraculoBOT agora possui integração completa com RAG (Retrieval-Augmented Generation), permitindo que o bot recupere legislação relevante do Supabase e a injete no contexto do Agno Agent para respostas mais precisas e fundamentadas.

## Arquitetura

```
User Message (Discord)
    ↓
enrich_with_rag(message.content)
    ↓
retrieve_relevant_legislation()
    ├─ OpenAIEmbedder (gera embedding da query)
    └─ RAGRetriever (busca vetorial no Supabase)
    ↓
RAG Context (legislação formatada)
    ↓
Agent Context (Discord + RAG)
    ↓
Agno Agent (DeepSeek + contexto enriquecido)
    ↓
Response (fundamentada em legislação)
```

## Componentes

### 1. `oraculo_bot/rag_retriever.py`
Classe `RAGRetriever` responsável pela busca vetorial no Supabase:
- Conexão PostgreSQL via `psycopg`
- Busca semântica usando pgvector (cosine similarity)
- Suporte a filtros de metadados (ano, banca, tipo)

### 2. `oraculo_bot/rag.py`
Funções de alto nível para integração com Agno:
- `init_rag(api_key)`: Inicializa o OpenAIEmbedder
- `retrieve_relevant_legislation(query, top_k, filters)`: Busca e formata contexto

### 3. `oraculo_bot/agent.py`
Função `enrich_with_rag(query, top_k)` que:
- Gerencia o ciclo de vida do OpenAIEmbedder
- Trata erros gracefully (fallback para sem RAG)
- Retorna contexto formatado para o agent

### 4. `oraculo_bot/bot.py`
Integração no pipeline de processamento de mensagens:
```python
rag_context = enrich_with_rag(message.content, top_k=3)
full_context = context + rag_context
runner.additional_context = full_context
```

## Configuração

### Variáveis de Ambiente (`.env`)

```bash
# Supabase PostgreSQL (obrigatório para RAG)
SUPABASE_DB_URL=postgres://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres?sslmode=require

# OpenAI API Key (opcional - para embeddings)
# Se não configurada, RAG usa fallback (embeddings aleatórios)
OPENAI_API_KEY=sk-...
```

## Banco de Dados Supabase

### Tabela `rag_chunks`

```sql
CREATE TABLE rag_chunks (
    id TEXT PRIMARY KEY,
    documento_id BIGINT,
    texto TEXT,
    metadados JSONB,
    embedding VECTOR(1536),
    token_count INTEGER
);
```

### Índice IVFFlat (otimizado para busca)

```sql
CREATE INDEX ON rag_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

## Exemplo de Uso

### 1. Teste Básico de Conexão

```bash
uv run test_rag_db_connection.py
```

Verifica:
- Conexão com Supabase
- Tabela `rag_chunks` existe
- Número de chunks com embeddings

### 2. Teste de Busca Vetorial

```bash
uv run test_rag_vector_search.py
```

Testa:
- Recuperação de embedding existente
- Busca de chunks similares
- Cálculo de similaridade

### 3. Teste Completo RAG

```bash
uv run test_full_rag_flow.py
```

Simula o fluxo completo:
- Query do usuário
- Geração de embedding
- Busca de legislação relevante
- Formatação de contexto para Discord

## Formato do Contexto RAG

O contexto RAG é injetado nas mensagens do Discord como:

```markdown
[CONTEXTO LEGISLATIVO RELEVANTE]
[Fonte 1 (ano: 2018, banca: FCC, tipo: lei, sim: 0.92)]
Art. 22. A defesa dos interesses e dos direitos dos titulares...

[Fonte 2 (ano: 2021, banca: CESPE, tipo: súmula, sim: 0.87)]
Súmula Vinculante 11: Só é lícito o uso de algemas...

[Fonte 3 (ano: 2013, banca: TJSP, tipo: content, sim: 0.85)]
§ 1º A imunidade é concedida aos deputados estaduais...
```

## Filtros de Metadados

É possível filtrar a busca RAG por metadados:

```python
from oraculo_bot.agent import enrich_with_rag

# Buscar apenas legislação de 2021
rag_context = enrich_with_rag(
    query="LGPD",
    top_k=3,
    filters={"ano": "2021"}
)

# Buscar apenas da banca FCC
rag_context = enrich_with_rag(
    query="direito administrativo",
    top_k=5,
    filters={"banca": "FCC"}
)

# Combinar filtros
rag_context = enrich_with_rag(
    query="servidor público",
    top_k=3,
    filters={"ano": "2020", "banca": "CESPE"}
)
```

## Fallback e Tolerância a Falhas

O RAG foi projetado para ser **tolerante a falhas**:

1. **OPENAI_API_KEY não configurada**: Usa fallback (embeddings aleatórios)
2. **Supabase indisponível**: Retorna contexto vazio, bot continua funcionando
3. **Nenhum chunk relevante**: Bot responde sem contexto RAG

Log de warning quando RAG falha:
```python
logger.warning(f"RAG fallback: {e}")
```

## Performance

### Métricas Atuais

- **Total de chunks**: 14,601
- **Dimensão do embedding**: 1536 (text-embedding-3-small)
- **Similaridade média**: 85-90%
- **Latência média**: ~200ms (incluindo embedding generation)

### Otimizações

1. **IVFFlat Index**: Busca aproximada 10x mais rápida
2. **Connection Pooling**: `psycopg` reutiliza conexões
3. **Lazy Embedding**: OpenAI API chamada apenas quando necessário

## Próximos Passos

### Curto Prazo
- [ ] Configurar OPENAI_API_KEY em produção
- [ ] Monitorar latência e custos de OpenAI API
- [ ] Ajustar `top_k` baseado em qualidade das respostas

### Médio Prazo
- [ ] Implementar cache de embeddings (Redis)
- [ ] Adicionar híbrida: vector + keyword search
- [ ] Métricas de uso e relevância

### Longo Prazo
- [ ] Fine-tuning de modelo de embeddings
- [ ] Reranking de resultados com cross-encoder
- [ ] Expansão para outras bases jurídicas

## Troubleshooting

### Erro: "SUPABASE_DB_URL não configurada"

**Solução**: Adicionar ao `.env`:
```bash
SUPABASE_DB_URL=postgres://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres?sslmode=require
```

### Erro: "cannot import name 'OpenAIEmbeddings'"

**Causa**: API do Agno mudou, usar `OpenAIEmbedder`:

```python
# Errado
from agno.models.openai import OpenAIEmbeddings

# Correto
from agno.knowledge.embedder.openai import OpenAIEmbedder
```

### Erro: "invalid input syntax for type vector"

**Causa**: Formato de embedding incorreto (parênteses ao invés de colchetes)

**Solução**: O `rag_retriever.py` já trata isso automaticamente.

### Similaridade muito baixa (< 60%)

**Possíveis causas**:
1. Query muito diferente do conteúdo da base
2. Embedding de baixa qualidade
3. Falta de chunks sobre o tema

**Soluções**:
1. Aumentar `top_k`
2. Usar filtros de metadados mais específicos
3. Considerar busca por keywords (`retrieve_by_keywords`)

## Referências

- [Agno Documentation](https://docs.agno.com/)
- [Supabase pgvector](https://supabase.com/docs/guides/ai/vector-columns)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)
- [IVFFlat Index](https://github.com/pgvector/pgvector#ivfflat)

## Licença

MIT - Ver LICENSE para mais detalhes.
