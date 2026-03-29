# RAG Jurídico Self-Hosted — Arquitetura, Decisões e Estado Atual

> **Nota:** este documento descreve o **schema de retrieval em produção** (`juridico.documents`, `juridico.chunks`, `juridico.content_links`, `juridico.match_chunks(...)`, `juridico.match_chunks_hybrid(...)`). O **schema de ingestão** do Lote 1 é separado e é definido pela migration `migrations/001_rag_lote1_ingestion_schema.sql` (`juridico.source_documents`, `juridico.document_chunks`, `juridico.ingestion_runs`, `juridico.retrieval_eval_runs`, `juridico.document_quarantine`). Retrieval e ingestão têm propósitos distintos.

## Resumo

Este projeto foi adaptado para usar um **Supabase self-hosted** com um schema dedicado chamado **`juridico`**.

A integração RAG do OraculoBOT não usa mais o desenho antigo baseado em `public.rag_*` como fonte principal. O padrão atual é:

- `juridico.documents`
- `juridico.chunks`
- `juridico.content_links`
- `juridico.match_chunks(...)`
- `juridico.match_chunks_hybrid(...)`

---

## Motivação da mudança

O banco estava funcional, mas organizado com cara de projeto único. Como a intenção passou a ser usar o mesmo Supabase self-hosted para mais de um projeto, foi feita a reorganização por domínio.

### Objetivos

- evitar transformar `public` em depósito geral
- separar o RAG jurídico em um schema próprio
- melhorar segurança com grants e RLS coerentes
- preparar o Supabase para múltiplos projetos futuros
- manter o legado antigo temporariamente sem quebrar nada à força

---

## Schema atual

### Schema canônico do RAG

#### `juridico.documents`
Tabela de documentos do corpus jurídico.

Campos principais:
- `id`
- `nome`
- `arquivo_origem`
- `content_hash`
- `schema_version`
- `chunk_count`
- `token_count`
- `created_at`

#### `juridico.chunks`
Tabela principal de recuperação.

Campos principais:
- `id`
- `document_id`
- `content`
- `metadata`
- `content_hash`
- `metadata_version`
- `token_count`
- `embedding`
- `search_text`
- `created_at`

#### `juridico.content_links`
Tabela para relacionamentos entre chunks.

Atualmente existe, mas está sem uso relevante em produção de dados.

---

## Segurança aplicada


### RLS

As tabelas do schema `juridico` têm RLS habilitada.


### Grants

O acesso foi restringido para evitar exposição acidental:

- `anon`: sem acesso às tabelas do RAG
- `authenticated`: sem acesso às tabelas do RAG
- `public`: sem acesso às tabelas do RAG
- `service_role`: acesso permitido


### Funções

As funções de recuperação do schema `juridico` foram fechadas para uso via backend/service role.


#### `juridico.match_chunks(...)`
- acesso: `service_role`


#### `juridico.match_chunks_hybrid(...)`
- acesso: `service_role`

### Search path de funções

O warning de `function_search_path_mutable` foi tratado.

Situação final:
- `public.match_rag_chunks` → corrigida
- `juridico.match_chunks` → corrigida
- `juridico.match_chunks_hybrid` → criada/ajustada com contexto seguro e compatível com pgvector

Observação importante:
- para a função híbrida, o `search_path` foi definido como `public, juridico`
- isso foi necessário para permitir a resolução correta do operador `<=>` do `pgvector`, instalado em `public`

---

## Extensões usadas

### `vector`
Usada para embeddings via pgvector.

Observação:
- a extensão `vector` está instalada no schema `public`
- isso gera warning de linter do Supabase (`extension_in_public`)
- **não foi movida**, porque essa migração é mais sensível e não era necessária para estabilizar o sistema

### `unaccent`
Habilitada para melhorar a recuperação textual em português.

---

## Busca pt-BR / busca híbrida

O sistema foi melhorado para português-BR com uma camada híbrida:

- busca vetorial por embeddings
- full-text search em português
- normalização com `unaccent`

### Coluna de FTS

Em `juridico.chunks` existe:
- `search_text tsvector`

Essa coluna é preenchida a partir de:
- `content` com peso maior
- `metadata::text` com peso menor

### Índice

Foi criado índice GIN para a coluna `search_text`.

### Trigger

Foi criado trigger para manter `search_text` atualizado em inserts/updates.

### Função híbrida

A função principal para recuperação híbrida é:

- `juridico.match_chunks_hybrid(query_text, query_embedding, ...)`

Ela combina:
- similaridade vetorial (`embedding <=> query_embedding`)
- ranking lexical (`ts_rank_cd`)
- score híbrido ponderado

Peso atual:
- 75% vetorial
- 25% lexical

---

## Benchmarks e ajustes feitos

### Índices criados por benchmark

Foram aplicados apenas os índices com ganho real ou justificativa clara:

- `ix_juridico_documents_nome`
- `ix_juridico_documents_arquivo_origem`
- `ix_juridico_content_links_linked_chunk_link_type`
- índice vetorial em `embedding`
- índice GIN em `metadata`
- índice GIN em `search_text`

### O que NÃO foi feito

Não foram aplicadas otimizações “por fé”, como:
- reescrever função de match sem benchmark
- trigger de contadores por linha
- partial indexes sem justificativa prática imediata

---

## Contadores corrigidos

Os campos derivados em `juridico.documents` estavam inconsistentes em relação a `juridico.chunks`.

Foi feita correção em lote de:
- `chunk_count`
- `token_count`

Resultado final:
- divergências zeradas no momento da correção

---

## Exposição segura do banco

O Postgres do Supabase self-hosted não estava acessível externamente por padrão.

Diagnóstico encontrado:
- banco ativo apenas em rede Docker interna
- sem publicação de porta no host
- firewall sem permitir acesso externo ao Postgres

### Ação aplicada

A porta `5432/tcp` foi publicada no host **com firewall restritivo**.

### Regra atual

Permitido apenas para:
- VPS OpenClaw: `84.247.186.181`

Negado para o restante da internet.

### Motivo

Permitir consumo do banco por serviços externos controlados (ex.: outra VPS do ecossistema), sem deixar o Postgres escancarado.

---

## Estado atual dos dados

No momento da validação:

- documentos: `1047`
- chunks: `18005`
- chunks com embedding: `18005`
- content_links: `0`
- total aproximado de tokens indexados: ~`9.8M`

---

## Smoke tests executados

### Passou

#### `test_rag_db_connection.py`
Valida:
- acesso ao Postgres
- existência da tabela
- existência de embeddings
- leitura de chunk de exemplo

#### `test_rag_retriever.py`
Valida:
- `RAGRetriever`
- uso da função híbrida
- recuperação de chunks semelhantes

#### `test_full_rag_flow.py`
Valida:
- query simulada
- embedding de entrada
- recuperação de contexto relevante
- geração do contexto que seria injetado no fluxo do bot

### Observação

O teste que depende de credencial real de embeddings/LLM pode falhar se a API key do ambiente não estiver válida.
Isso não invalida a camada de RAG já validada por smoke test técnico e leitura direta do banco.

---

## Arquitetura do OraculoBOT após adaptação

### Retriever principal

Arquivo:
- `oraculo_bot/rag_retriever.py`

Situação atual:
- usa `juridico.match_chunks_hybrid(...)` como caminho principal
- usa `juridico.chunks` para fallback por keyword
- mantém payload compatível com chaves antigas e novas para reduzir atrito no restante do código

### Convenção de payload

O retriever retorna, quando aplicável, ambos os formatos:

- legado:
  - `documento_id`
  - `texto`
  - `metadados`

- novo:
  - `document_id`
  - `content`
  - `metadata`

Isso foi mantido como camada de compatibilidade.

---

## Pull Request relacionado

PR principal da migração/adaptação:

- `feat: adapt OraculoBOT to juridico RAG schema`

Branch já foi mergeada e removida depois da revisão.

---

## Próximos passos recomendados

### Curto prazo

- testar o bot em ambiente real no Discord
- validar qualidade das respostas com perguntas jurídicas reais
- observar quando o ranking lexical ajuda ou atrapalha

### Médio prazo

- decidir se `content_links` vai mesmo entrar em uso
- avaliar se campos importantes do `metadata` devem virar colunas explícitas
- revisar buckets/storage se houver ingestão documental mais pesada

### Longo prazo

- se o Supabase virar hub de muitos projetos, continuar organizando por schema
- só considerar múltiplas instâncias self-hosted quando houver necessidade real de isolamento forte

---

## Resumo executivo

Estado atual do sistema:

- banco organizado por schema: **sim**
- segurança melhorada: **sim**
- acesso externo controlado ao Postgres: **sim**
- busca vetorial funcionando: **sim**
- busca híbrida pt-BR funcionando: **sim**
- smoke test técnico do RAG/OraculoBOT: **sim**
- legado antigo removido do banco: **não** (mantido temporariamente)

Em português claro:

O RAG jurídico self-hosted do OraculoBOT saiu do estágio “promissor” e entrou no estágio **realmente utilizável**.
