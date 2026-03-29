# IMPLEMENTATION_TODO — Pipeline de Ingestão do RAG Lote 1

## Objetivo

Este arquivo quebra a implementação do pipeline de ingestão do **Lote 1** em tarefas concretas de código.

Ele existe para evitar o padrão clássico de projeto técnico mal conduzido:
- alguém lê a documentação por cima
- começa a codar do meio
- inventa arquitetura no susto
- mistura ingestão, classificação, embedding e retrieval
- e depois todo mundo chama o caos de “MVP”

Aqui não.

---

## Leitura obrigatória antes de codar

Antes de executar qualquer tarefa abaixo, leia nesta ordem:

1. `README.md`
2. `PASSO_2_CLASSIFICACAO_OPERACIONAL.md`
3. `PASSO_3_ESTRATEGIA_INGESTAO.md`
4. `PASSO_4_PLANO_TECNICO_EXECUTAVEL.md`
5. `PASSO_5_ESPECIFICACAO_IMPLEMENTACAO.md`

Se a implementação conflitar com esses documentos, **pare e alinhe**. Não improvise.

---

## Escopo da primeira entrega

A **primeira entrega útil** é esta:

> Conseguir ingerir o bloco lógico `eleitoral` de ponta a ponta com rastreabilidade, metadados, embeddings e teste mínimo de recuperação.

Se ainda não faz isso, não avance para os blocos mais confusos.

---

## Ordem macro de implementação

1. infraestrutura de persistência
2. descoberta de arquivos
3. extração de texto
4. classificação documental
5. detecção de sinais didáticos
6. chunking estruturado
7. score heurístico
8. persistência de chunks
9. embeddings/indexação
10. avaliação de recuperação
11. runner da ingestão
12. primeiro run: `eleitoral`

---

# EPIC 1 — Infraestrutura de persistência

## Tarefa 1.1 — Criar modelos/entidades do pipeline

### Objetivo
Adicionar as entidades mínimas do pipeline descritas no Passo 5.

### Entidades mínimas
- `ingestion_runs`
- `source_documents`
- `document_chunks`
- `retrieval_eval_runs`
- `document_quarantine` (recomendado)

### Entregáveis
- modelos Python / ORM / dataclasses / structs equivalentes
- enums de status e taxonomia
- tipos consistentes para campos obrigatórios

### Critério de aceite
- entidades existentes no código
- campos obrigatórios cobertos
- enums não estão hardcoded em 12 lugares diferentes

---

## Tarefa 1.2 — Criar migração/schema SQL

### Objetivo
Persistir as entidades no banco do schema `juridico`.

### Entregáveis
- script SQL ou migração equivalente
- índices básicos por `run_key`, `ramo`, `bloco_logico`, `autoridade`, `status`
- estrutura preparada para campo vetorial

### Critério de aceite
- schema sobe sem erro
- rollback da migração é possível
- índices principais existem

### Observação
Não faz gambiarra de criar tabela “temporária que depois a gente vê”. Isso sempre vira permanente.

---

## Tarefa 1.3 — Criar camada de repositório/persistência

### Objetivo
Centralizar operações de gravação/leitura do pipeline.

### Funções mínimas esperadas
- `create_ingestion_run(...)`
- `finalize_ingestion_run(...)`
- `register_source_document(...)`
- `update_document_extraction(...)`
- `update_document_classification(...)`
- `save_chunk(...)`
- `save_eval_result(...)`
- `move_document_to_quarantine(...)`

### Critério de aceite
- pipeline não grava SQL espalhado em todo arquivo
- operações principais estão encapsuladas

---

# EPIC 2 — Descoberta de arquivos

## Tarefa 2.1 — Implementar scanner do Lote 1

### Objetivo
Descobrir arquivos nas pastas físicas do lote.

### Entradas esperadas
- raiz do corpus
- lista de pastas do lote

### Saída esperada
Manifesto com:
- caminho absoluto
- nome do arquivo
- extensão
- tamanho
- hash SHA-256
- pasta física de origem

### Critério de aceite
- scanner percorre pastas corretamente
- ignora diretórios irrelevantes
- não perde rastreabilidade do caminho original

---

## Tarefa 2.2 — Gerar manifesto versionado

### Objetivo
Salvar a descoberta de arquivos como artefato auditável.

### Entregáveis
- `manifest.csv` ou `manifest.jsonl`
- vínculo com `run_key`
- suporte a reprocessamento

### Critério de aceite
- cada run gera manifesto próprio
- manifesto permite reproduzir a rodada

---

## Tarefa 2.3 — Deduplicação inicial por hash

### Objetivo
Evitar ingestão redundante óbvia.

### Regra
- duplicata exata por hash deve ser marcada
- não descartar silenciosamente

### Critério de aceite
- duplicatas são detectadas e registradas
- decisão de uso/quarentena fica explícita

---

# EPIC 3 — Extração de texto

## Tarefa 3.1 — Implementar extractor por tipo de arquivo

### Objetivo
Extrair texto bruto mantendo status e método de extração.

### Suporte inicial mínimo
- PDF texto
- DOCX
- TXT/MD
- fallback para OCR se necessário

### Campos de saída
- `texto_extraido`
- `extracao_status`
- `extracao_metodo`
- `char_count`

### Critério de aceite
- documentos válidos produzem texto utilizável
- falhas ficam registradas

---

## Tarefa 3.2 — Detectar extração ruim

### Objetivo
Identificar documentos com texto inútil.

### Heurísticas mínimas
- texto vazio
- texto muito curto
- proporção absurda de caracteres quebrados/lixo

### Critério de aceite
- documentos ruins não seguem automaticamente no pipeline
- status vira `quarentena` ou `revisao_manual`

---

## Tarefa 3.3 — Persistir artefato de texto bruto

### Objetivo
Permitir auditoria/reprocessamento sem reextrair sempre.

### Entregáveis
- armazenamento em staging ou tabela apropriada
- vínculo com `source_document`

### Critério de aceite
- texto bruto fica rastreável por documento

---

# EPIC 4 — Classificação documental

## Tarefa 4.1 — Implementar inferência de `bloco_logico`

### Objetivo
Converter pasta física em bloco lógico quando necessário.

### Casos críticos
- `eca_e_educacao` → `eca` ou `educacao`
- `constitucional_direitos_humanos_internacional` → `constitucional`, `direitos_humanos` ou `internacional`

### Critério de aceite
- lógica não depende só do nome da pasta
- casos mistos ficam tratáveis

---

## Tarefa 4.2 — Implementar classificador de `fonte_tipo`

### Objetivo
Inferir `lei`, `resolucao`, `decreto`, `convencao`, `material_de_apoio` etc.

### Sinais possíveis
- nome do arquivo
- headings do texto
- padrões jurídicos recorrentes

### Critério de aceite
- arquivos óbvios são classificados corretamente
- casos duvidosos são marcados como ambíguos, não chutados

---

## Tarefa 4.3 — Implementar classificador de `autoridade`

### Objetivo
Inferir `planalto`, `tse`, `stf`, `oea`, `onu`, etc.

### Critério de aceite
- principais autoridades do Lote 1 são inferidas com consistência
- `desconhecida` existe e é usada quando necessário

---

## Tarefa 4.4 — Implementar cálculo inicial de `peso_confianca`

### Objetivo
Aplicar a escala `alto`, `medio`, `baixo` com base no tipo documental.

### Critério de aceite
- lei oficial não cai como `baixo`
- material editorializado não entra como `alto`

---

## Tarefa 4.5 — Implementar status de ambiguidade

### Objetivo
Marcar documentos que exigem revisão manual.

### Saída esperada
- `status_documento = revisao_manual` ou `quarentena`
- `motivo_status`

### Critério de aceite
- casos ambíguos não são empurrados pipeline adentro como se estivesse tudo certo

---

# EPIC 5 — Sinais didáticos e anotação

## Tarefa 5.1 — Detectar `#Atenção` / `#Atencao`

### Objetivo
Marcar trechos e documentos com destaque didático.

### Implementação mínima
- regex case-insensitive
- detecção em nível de documento e chunk

### Critério de aceite
- documentos com marcação são identificados corretamente

---

## Tarefa 5.2 — Detectar `tem_anotacao`

### Objetivo
Inferir se o material é anotado/grifado/comentado.

### Critério de aceite
- legislação seca e material comentado não ficam indistintos

---

# EPIC 6 — Chunking estruturado

## Tarefa 6.1 — Criar chunker jurídico estrutural

### Objetivo
Quebrar o texto respeitando estrutura normativa.

### Ordem de preferência
- artigo
- parágrafo
- inciso/alínea
- seção/subtítulo
- fallback por tamanho

### Critério de aceite
- chunks não quebram o texto de forma burra quando existe estrutura legal clara

---

## Tarefa 6.2 — Implementar fallback por tamanho com overlap

### Objetivo
Cobrir documentos sem estrutura detectável.

### Parâmetros iniciais sugeridos
- alvo: 600–1200 tokens
- overlap: 80–150 tokens

### Critério de aceite
- fallback funciona sem gerar chunks gigantescos ou inúteis

---

## Tarefa 6.3 — Separar norma e comentário quando possível

### Objetivo
Evitar chunk híbrido bagunçado em materiais anotados.

### Critério de aceite
- quando a estrutura deixar claro, texto-base e comentário não ficam colados artificialmente

---

## Tarefa 6.4 — Gerar metadados por chunk

### Objetivo
Persistir chunk já enriquecido com herança documental.

### Campos mínimos
- `ordem_chunk`
- `texto_chunk`
- `artigo_ref`
- `titulo_secao`
- `ramo`
- `fonte_tipo`
- `autoridade`
- `tem_anotacao`
- `tem_atencao`
- `peso_confianca`

### Critério de aceite
- cada chunk sai pronto para score + embedding + retrieval

---

# EPIC 7 — Score operacional

## Tarefa 7.1 — Implementar `prioridade_recuperacao`

### Objetivo
Calcular score heurístico inicial conforme Passo 5.

### Fatores mínimos
- `peso_confianca`
- `fonte_tipo`
- `autoridade`
- `tem_atencao`
- `tem_anotacao`
- penalização editorial

### Critério de aceite
- score reproduz lógica documental esperada
- fonte oficial continua acima de material fraco em condições normais

---

## Tarefa 7.2 — Criar testes unitários do score

### Objetivo
Evitar regressão besta de ranking.

### Casos obrigatórios
- lei oficial > material de apoio anotado
- resolução TSE > questão comentada
- `#Atenção` melhora score relativo sem inverter autoridade forte

### Critério de aceite
- testes cobrindo conflitos principais do modelo

---

# EPIC 8 — Embeddings e indexação

## Tarefa 8.1 — Integrar geração de embeddings por chunk

### Objetivo
Gerar embedding para `document_chunks` aprovados.

### Critério de aceite
- geração por lote funciona
- falha de embedding não corrompe a run inteira silenciosamente

---

## Tarefa 8.2 — Persistir status de embedding

### Objetivo
Rastrear chunks pendentes, gerados ou falhos.

### Critério de aceite
- `embedding_status` atualizado corretamente

---

## Tarefa 8.3 — Garantir filtro por metadados no retrieval

### Objetivo
Permitir busca com filtros por:
- `ramo`
- `bloco_logico`
- `fonte_tipo`
- `autoridade`

### Critério de aceite
- retrieval não depende só de vetor bruto
- dá para segurar contaminação semântica cruzada

---

# EPIC 9 — Avaliação de recuperação

## Tarefa 9.1 — Criar suíte mínima de queries canônicas

### Objetivo
Formalizar queries de teste por bloco lógico.

### Primeira suíte obrigatória
- bloco `eleitoral`

### Critério de aceite
- queries ficam versionadas e reproduzíveis

---

## Tarefa 9.2 — Implementar executor de avaliação

### Objetivo
Rodar queries e salvar top-k + resultado.

### Saída mínima
- query
- top 10
- resultado (`pass`, `warning`, `fail`)
- observação

### Critério de aceite
- avaliação produz artefato persistido, não só print bonito no terminal

---

## Tarefa 9.3 — Implementar gate de aprovação da run

### Objetivo
Fechar a rodada como:
- `validated`
- `failed`
- `rolled_back`

### Critério de aceite
- decisão final da rodada é calculável e auditável

---

# EPIC 10 — Runner end-to-end

## Tarefa 10.1 — Criar comando/entrypoint de ingestão

### Objetivo
Executar o pipeline por bloco lógico.

### Exemplo de interface desejável
```bash
uv run python -m oraculo_bot.ingestion run --bloco eleitoral --run-key lote1_v1_eleitoral
```

### Critério de aceite
- execução por bloco funciona sem editar código na mão

---

## Tarefa 10.2 — Adicionar modo dry-run

### Objetivo
Permitir validação sem gravar embeddings ou sem persistência final completa.

### Critério de aceite
- dry-run útil de verdade
- não é placebo que faz metade das writes escondidas

---

## Tarefa 10.3 — Adicionar relatórios por rodada

### Objetivo
Emitir relatório humano + estruturado.

### Entregáveis
- markdown
- json

### Critério de aceite
- cada run deixa rastro claro do que aconteceu

---

# EPIC 11 — Quarentena e rollback

## Tarefa 11.1 — Implementar quarentena documental

### Objetivo
Segurar documentos ruins fora do fluxo principal.

### Critério de aceite
- documento problemático não vai parar no índice principal por acidente

---

## Tarefa 11.2 — Implementar rollback por `run_key`

### Objetivo
Desfazer uma ingestão ruim.

### Critério de aceite
- chunks/documentos da run podem ser invalidados/removidos do índice
- motivo e timestamp ficam registrados

---

# EPIC 12 — Primeiro alvo real: `eleitoral`

## Tarefa 12.1 — Preparar a run `lote1_v1_eleitoral`

### Objetivo
Executar a primeira rodada real do pipeline.

### Checklist
- [ ] manifesto gerado
- [ ] extração validada
- [ ] classificação revisada por amostragem
- [ ] chunking validado
- [ ] score aplicado
- [ ] embeddings gerados
- [ ] retrieval testado
- [ ] relatório emitido

### Critério de aceite
- run final do eleitoral concluída com decisão explícita

---

## Tarefa 12.2 — Revisar aprendizado e ajustar pipeline

### Objetivo
Usar `eleitoral` como prova de fogo antes de avançar.

### Saída esperada
- lista de bugs
- ajustes de heurística
- ajustes de chunking
- ajustes de score

### Critério de aceite
- pipeline melhora antes de entrar em `administrativo`

---

# Testes obrigatórios

## Unitários
Cobrir no mínimo:
- inferência de `bloco_logico`
- inferência de `fonte_tipo`
- inferência de `autoridade`
- score heurístico
- detecção de `#Atenção`
- chunking estrutural

## Integração
Cobrir no mínimo:
- criação de `ingestion_run`
- persistência de `source_document`
- persistência de `document_chunks`
- quarentena
- avaliação

## E2E mínimo
Cobrir no mínimo:
- run completa do bloco `eleitoral` em amostra pequena

---

# Ordem recomendada de PRs/commits

## PR 1
Schema + modelos + repositórios

## PR 2
Scanner + manifesto + extração

## PR 3
Classificação documental + sinais didáticos

## PR 4
Chunking + score

## PR 5
Embeddings + filtros + retrieval eval

## PR 6
Runner end-to-end + relatórios + rollout inicial do eleitoral

---

# Não fazer

- não começar por constitucional/internacional
- não ingerir tudo num batch cego
- não esconder documento ruim dentro do índice
- não tratar `#Atenção` como autoridade jurídica
- não espalhar regra de classificação em arquivos aleatórios
- não misturar lógica de ingestão com lógica do bot de resposta se isso puder ser modularizado
- não chamar de pronto sem avaliação de recuperação

---

# Definition of Done da primeira versão

A v1 do pipeline só está pronta quando:

- existe comando de ingestão por bloco lógico
- existe persistência auditável por `run_key`
- existe quarentena
- existe chunking com metadados
- existe score inicial
- existe embedding por chunk
- existe teste de recuperação
- `eleitoral` roda de ponta a ponta

Se isso ainda não aconteceu, o resto é conversa bonita.
