# IMPLEMENTATION_STATUS — Pipeline de Ingestão do RAG Lote 1

## Objetivo

Este arquivo serve para acompanhar o **estado real da implementação** do pipeline de ingestão do Lote 1.

Ele não é documentação conceitual.
Ele é controle operacional.

Use para marcar:
- o que já foi implementado
- o que está em andamento
- o que está bloqueado
- o que foi validado de verdade

Se não estiver marcado aqui, assuma que **não está pronto**.

---

## Convenção de status

Use estes marcadores:

- `[ ]` não iniciado
- `[-]` em andamento
- `[x]` concluído
- `[!]` bloqueado
- `[?]` precisa validar

---

## Leitura obrigatória associada

Antes de atualizar este status, conferir:
- `README.md`
- `PASSO_2_CLASSIFICACAO_OPERACIONAL.md`
- `PASSO_3_ESTRATEGIA_INGESTAO.md`
- `PASSO_4_PLANO_TECNICO_EXECUTAVEL.md`
- `PASSO_5_ESPECIFICACAO_IMPLEMENTACAO.md`
- `IMPLEMENTATION_TODO.md`

---

## Regra de atualização

Ao concluir uma tarefa, atualizar este arquivo com:
- status
- data
- referência de commit/PR, se houver
- observação curta

Modelo:

```text
[x] Tarefa X.Y — 2026-03-28 — commit abc1234
Observação: ...
```

---

# STATUS GERAL

## Situação atual

- Documentação do pipeline Lote 1: `[x]`
- TODO técnico quebrado em tarefas: `[x]`
- Implementação de código: `[-]`
- Primeiro bloco rodando ponta a ponta (`eleitoral`): `[ ]`

---

# EPIC 1 — Infraestrutura de persistência

## 1.1 Modelos/entidades do pipeline
- [x] `ingestion_runs`
- [x] `source_documents`
- [x] `document_chunks`
- [x] `retrieval_eval_runs`
- [x] `document_quarantine`

Observações:
- [x] 2026-03-28 — modelos e enums adicionados em `oraculo_bot/ingestion/models.py`

## 1.2 Migração/schema SQL
- [x] script/migração criada
- [x] índices principais criados
- [x] migração validada no banco real
- [ ] rollback da migração validado

Observações:
- [x] 2026-03-30 — migration aplicada e validada no Postgres real do Supabase (tabelas, enums, extensões `pgcrypto`/`vector`, índices-chave e trigger function confirmados)
- [ ] rollback completo da migration ainda não validado em ambiente isolado

## 1.3 Camada de persistência/repositório
- [x] `create_ingestion_run(...)`
- [x] `finalize_ingestion_run(...)`
- [x] `register_source_document(...)`
- [x] `update_document_extraction(...)`
- [x] `update_document_classification(...)`
- [x] `save_chunk(...)`
- [x] `save_eval_result(...)`
- [x] `move_document_to_quarantine(...)`

---

# EPIC 2 — Descoberta de arquivos

## 2.1 Scanner do Lote 1

- [x] scanner implementado
- [x] percorre pastas físicas corretamente
- [x] preserva caminho original

## 2.2 Manifesto versionado

- [x] manifesto gerado por run
- [x] manifesto persistido em staging ou equivalente
- [x] manifesto reproduz a rodada

## 2.3 Deduplicação inicial por hash

- [x] hash SHA-256 calculado
- [x] duplicatas detectadas
- [x] duplicatas registradas com status explícito

---

# EPIC 3 — Extração de texto

## 3.1 Extractor por tipo de arquivo
- [x] PDF texto
- [x] DOCX
- [x] TXT/MD
- [x] fallback OCR

## 3.2 Detecção de extração ruim
- [x] texto vazio detectado
- [x] texto muito curto detectado
- [x] texto corrompido/lixo detectado
- [x] documentos ruins desviados do fluxo principal

## 3.3 Persistência do texto bruto
- [x] texto bruto salvo com rastreabilidade
- [x] vínculo com `source_document`

Observações:
- [x] 2026-03-30 — extractor, detecção de texto ruim e rastreabilidade implementados no PR 2 (`fb67ec2`, `261537b`)

---

# EPIC 4 — Classificação documental

## 4.1 Inferência de `bloco_logico`
- [ ] `eca_e_educacao` separado corretamente
- [ ] `constitucional_direitos_humanos_internacional` separado corretamente
- [ ] regra não depende só da pasta física

## 4.2 Classificador de `fonte_tipo`

- [ ] `lei`
- [ ] `resolucao`
- [ ] `decreto`
- [ ] `convencao`
- [ ] `material_de_apoio`
- [ ] ambiguidade tratada corretamente

## 4.3 Classificador de `autoridade`
- [ ] `planalto`
- [ ] `tse`
- [ ] `stf`
- [ ] `stj`
- [ ] `oea`
- [ ] `onu`
- [ ] `desconhecida`

## 4.4 Cálculo de `peso_confianca`

- [ ] `alto`
- [ ] `medio`
- [ ] `baixo`
- [ ] coerência validada por amostragem

## 4.5 Tratamento de ambiguidade

- [ ] `revisao_manual`
- [ ] `quarentena`
- [ ] `motivo_status`

---

# EPIC 5 — Sinais didáticos e anotação

## 5.1 Detecção de `#Atenção`
- [ ] `#Atenção`
- [ ] `#Atencao`
- [ ] marcação em nível de documento
- [ ] marcação em nível de chunk

## 5.2 Detecção de `tem_anotacao`
- [ ] heurística implementada
- [ ] legislação seca ≠ material anotado

---

# EPIC 6 — Chunking estruturado

## 6.1 Chunker jurídico estrutural
- [ ] quebra por artigo
- [ ] quebra por parágrafo/inciso
- [ ] quebra por seção/subtítulo

## 6.2 Fallback por tamanho com overlap
- [ ] fallback implementado
- [ ] overlap configurado
- [ ] chunks não ficam gigantes/inúteis

## 6.3 Separação entre norma e comentário
- [ ] regra implementada quando a estrutura permitir

## 6.4 Metadados por chunk
- [ ] `ordem_chunk`
- [ ] `texto_chunk`
- [ ] `artigo_ref`
- [ ] `titulo_secao`
- [ ] `ramo`
- [ ] `fonte_tipo`
- [ ] `autoridade`
- [ ] `tem_anotacao`
- [ ] `tem_atencao`
- [ ] `peso_confianca`

---

# EPIC 7 — Score operacional

## 7.1 `prioridade_recuperacao`
- [ ] score heurístico implementado
- [ ] autoridade documental preservada
- [ ] `#Atenção` melhora score relativo sem bagunçar hierarquia

## 7.2 Testes do score
- [ ] lei oficial > material de apoio anotado
- [ ] resolução TSE > questão comentada
- [ ] `#Atenção` não atropela fonte superior

---

# EPIC 8 — Embeddings e indexação

## 8.1 Geração de embeddings por chunk
- [ ] embeddings gerados por lote
- [ ] falhas registradas corretamente

## 8.2 Status de embedding
- [ ] `pendente`
- [ ] `gerado`
- [ ] `falha`

## 8.3 Filtro por metadados no retrieval
- [ ] filtro por `ramo`
- [ ] filtro por `bloco_logico`
- [ ] filtro por `fonte_tipo`
- [ ] filtro por `autoridade`

---

# EPIC 9 — Avaliação de recuperação

## 9.1 Suíte de queries canônicas
- [ ] queries de `eleitoral`
- [ ] queries versionadas
- [ ] queries reproduzíveis

## 9.2 Executor de avaliação
- [ ] roda top-k
- [ ] salva resultado
- [ ] salva observação

## 9.3 Gate de aprovação da run
- [ ] `validated`
- [ ] `failed`
- [ ] `rolled_back`

---

# EPIC 10 — Runner end-to-end

## 10.1 Command/entrypoint de ingestão
- [ ] runner por bloco lógico
- [ ] `run_key` parametrizável
- [ ] sem necessidade de editar código manualmente

## 10.2 Modo dry-run
- [ ] dry-run implementado
- [ ] dry-run sem writes escondidas indevidas

## 10.3 Relatórios por rodada
- [ ] markdown
- [ ] json
- [ ] artefatos persistidos

---

# EPIC 11 — Quarentena e rollback

## 11.1 Quarentena documental
- [ ] documento ruim fica fora do fluxo principal
- [ ] motivo registrado
- [ ] revisão possível

## 11.2 Rollback por `run_key`
- [ ] rollback lógico implementado
- [ ] chunks/documentos da run podem ser invalidados
- [ ] motivo e timestamp registrados

---

# EPIC 12 — Primeiro alvo real: `eleitoral`

## 12.1 Run `lote1_v1_eleitoral`
- [ ] manifesto gerado
- [ ] extração validada
- [ ] classificação revisada por amostragem
- [ ] chunking validado
- [ ] score aplicado
- [ ] embeddings gerados
- [ ] retrieval testado
- [ ] relatório emitido
- [ ] decisão final registrada

## 12.2 Aprendizado pós-run
- [ ] bugs listados
- [ ] heurísticas ajustadas
- [ ] chunking ajustado
- [ ] score ajustado
- [ ] pipeline pronto para `administrativo`

---

# TESTES

## Unitários
- [ ] inferência de `bloco_logico`
- [ ] inferência de `fonte_tipo`
- [ ] inferência de `autoridade`
- [x] score heurístico
- [ ] detecção de `#Atenção`
- [ ] chunking estrutural

## Integração
- [ ] criação de `ingestion_run`
- [ ] persistência de `source_document`
- [ ] persistência de `document_chunks`
- [ ] quarentena
- [ ] avaliação

## E2E mínimo
- [ ] run completa de amostra pequena do bloco `eleitoral`

---

# PRs / Entregas recomendadas

## PR 1
- [x] Schema + modelos + repositórios

## PR 2
- [ ] Scanner + manifesto + extração

## PR 3
- [ ] Classificação documental + sinais didáticos

## PR 4
- [ ] Chunking + score

## PR 5
- [ ] Embeddings + filtros + retrieval eval

## PR 6
- [ ] Runner end-to-end + relatórios + rollout inicial do eleitoral

---

# BLOQUEIOS / RISCOS

Use esta seção para registrar problemas reais.

## Bloqueios atuais
- [ ] Nenhum bloqueio registrado ainda

## Riscos já conhecidos
- [ ] Pastas mistas contaminarem classificação semântica
- [ ] Chunking ruim gerar recuperação confusa
- [ ] `#Atenção` ser usado para inflar fonte fraca indevidamente
- [ ] Falta de filtro por metadado bagunçar constitucional/internacional

---

# CHANGELOG OPERACIONAL

## 2026-03-28
- [x] Documentação do pipeline Lote 1 criada
- [x] `IMPLEMENTATION_TODO.md` criado
- [x] `IMPLEMENTATION_STATUS.md` criado
- [x] Base do PR 1 criada: modelos, repositório e migration SQL
- [x] Testes unitários básicos materializados em `test_models.py` e `test_repository.py`
- [ ] Migration ainda não validada contra banco real
- [ ] Testes de integração/E2E ainda não feitos

---

# Definition of Done da v1

A v1 só está pronta quando todos estes itens forem verdadeiros:

- [ ] existe comando de ingestão por bloco lógico
- [ ] existe persistência auditável por `run_key`
- [ ] existe quarentena
- [ ] existe chunking com metadados
- [ ] existe score inicial
- [ ] existe embedding por chunk
- [ ] existe teste de recuperação
- [ ] `eleitoral` roda de ponta a ponta

Se isso ainda não estiver marcado, então ainda não está pronto. Simples.

Observações:
- [x] 2026-03-30 — extractor implementado em oraculo_bot/ingestion/extractor.py
- [x] 2026-03-30 — detector de texto ruim implementado com heurísticas configuráveis
- [x] 2026-03-30 — ResultadoExtracao rastreável, vinculado ao caminho do documento
- [x] 2026-03-30 — Testes unitários para scanner, manifest e extractor passando

# PR 2 — Scanner + manifesto + extração

- [x] Scanner + manifesto + extração
- [x] 2026-03-30 — EPIC 2 (scanner, manifesto, deduplicação) implementado
- [x] 2026-03-30 — EPIC 3 (extração e detecção de texto ruim) implementado
- [x] 2026-03-30 — test_scanner.py: 20 testes passando
- [x] 2026-03-30 — test_manifest.py: 13 testes passando
- [x] 2026-03-30 — test_extractor.py: 20 testes passando
