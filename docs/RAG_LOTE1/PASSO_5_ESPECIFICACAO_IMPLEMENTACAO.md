# Passo 5 — Especificação de Implementação do Pipeline de Ingestão do Lote 1

## Objetivo

Definir a especificação concreta para implementação do pipeline do Lote 1 no schema `juridico`, incluindo:

- modelo de dados
- campos obrigatórios
- estados do processamento
- pseudocódigo do pipeline
- regras iniciais de score/ranking
- formato dos relatórios operacionais

Aqui a conversa deixa de ser conceitual e vira especificação que alguém consegue codar sem inventar moda no meio do caminho.

---

## Escopo desta especificação

Esta especificação cobre o pipeline de ingestão para os blocos lógicos:

1. `eleitoral`
2. `administrativo`
3. `penal`
4. `consumidor`
5. `eca`
6. `educacao`
7. `constitucional`
8. `direitos_humanos`
9. `internacional`

Ela parte do pressuposto de que:
- o Passo 2 definiu a taxonomia
- o Passo 3 definiu a ordem de ingestão
- o Passo 4 definiu o plano técnico executável

---

## Princípios de implementação

1. **Rastreabilidade total**
   - todo chunk precisa apontar para documento, arquivo e versão de ingestão

2. **Versionamento explícito**
   - nenhuma rodada importante deve sobrescrever estado antigo sem controle

3. **Filtro por metadados é obrigatório**
   - não basta embedding; precisa filtro por ramo, autoridade e tipo

4. **Quarentena é parte do sistema**
   - documento ambíguo ou ruim não entra por default

5. **Autoridade documental vem antes de destaque didático**
   - `#Atenção` melhora ranking relativo, não hierarquia jurídica

---

## Modelo de dados recomendado

A implementação mínima deve ter 4 entidades principais:

1. `ingestion_runs`
2. `source_documents`
3. `document_chunks`
4. `retrieval_eval_runs`

Opcional, mas muito útil:
5. `document_quarantine`
6. `classification_reviews`

---

## Tabela 1 — `ingestion_runs`

## Finalidade
Registrar cada rodada de ingestão de forma auditável.

### Campos recomendados
- `id` — UUID
- `run_key` — texto único, ex.: `lote1_v1_eleitoral`
- `lote` — ex.: `lote1`
- `bloco_logico` — ex.: `eleitoral`
- `pasta_origem` — texto
- `status` — `planned`, `running`, `validated`, `failed`, `rolled_back`
- `started_at` — timestamp
- `finished_at` — timestamp nullable
- `created_by` — texto
- `observacoes` — texto nullable
- `stats_json` — json/jsonb nullable

### Índices recomendados
- índice único em `run_key`
- índice em `bloco_logico`
- índice em `status`

---

## Tabela 2 — `source_documents`

## Finalidade
Representar o documento fonte antes e depois da extração/classificação.

### Campos obrigatórios
- `id` — UUID
- `ingestion_run_id` — FK para `ingestion_runs`
- `documento_id_externo` — texto único por run ou hash derivado
- `arquivo_origem` — texto
- `arquivo_nome` — texto
- `pasta_origem` — texto
- `bloco_logico` — texto
- `hash_sha256` — texto
- `extensao` — texto
- `tamanho_bytes` — bigint
- `texto_extraido` — texto nullable
- `extracao_status` — `ok`, `parcial`, `falha`
- `extracao_metodo` — texto nullable
- `ramo` — texto
- `fonte_tipo` — texto
- `autoridade` — texto
- `tem_anotacao` — boolean
- `tem_atencao_documento` — boolean
- `peso_confianca` — `alto`, `medio`, `baixo`
- `ano` — integer nullable
- `banca` — texto nullable
- `subtema` — texto nullable
- `tipo` — texto nullable
- `status_documento` — `aprovado`, `quarentena`, `descartado`, `revisao_manual`
- `motivo_status` — texto nullable
- `created_at` — timestamp
- `updated_at` — timestamp

### Índices recomendados
- índice em `ingestion_run_id`
- índice em `bloco_logico`
- índice em `ramo`
- índice em `fonte_tipo`
- índice em `autoridade`
- índice em `status_documento`
- índice em `hash_sha256`

### Observações
- `documento_id_externo` pode ser derivado de hash + caminho normalizado
- `texto_extraido` pode ficar fora da tabela se o volume for absurdo, mas para a primeira versão pode ficar aqui sem drama

---

## Tabela 3 — `document_chunks`

## Finalidade
Armazenar a unidade real de recuperação.

### Campos obrigatórios
- `id` — UUID
- `ingestion_run_id` — FK
- `source_document_id` — FK
- `chunk_id_externo` — texto único
- `ordem_chunk` — integer
- `texto_chunk` — texto
- `titulo_secao` — texto nullable
- `artigo_ref` — texto nullable
- `ramo` — texto
- `bloco_logico` — texto
- `fonte_tipo` — texto
- `autoridade` — texto
- `arquivo_origem` — texto
- `pasta_origem` — texto
- `tem_anotacao` — boolean
- `tem_atencao` — boolean
- `tipo_marcacao` — texto nullable
- `relevancia_estudo` — texto nullable
- `peso_confianca` — `alto`, `medio`, `baixo`
- `ano` — integer nullable
- `banca` — texto nullable
- `subtema` — texto nullable
- `tipo` — texto nullable
- `prioridade_recuperacao` — numeric or integer
- `status_validacao` — `pendente`, `aprovado`, `rejeitado`
- `embedding_status` — `pendente`, `gerado`, `falha`
- `embedding_model` — texto nullable
- `embedding_vector` — vetor/coluna específica do banco, se houver
- `created_at` — timestamp
- `updated_at` — timestamp

### Índices recomendados
- índice em `source_document_id`
- índice em `ingestion_run_id`
- índice em `ramo`
- índice em `bloco_logico`
- índice em `fonte_tipo`
- índice em `autoridade`
- índice em `tem_atencao`
- índice em `peso_confianca`
- índice em `status_validacao`

### Índices vetoriais
Depende do stack, mas precisa existir no campo de embedding.

---

## Tabela 4 — `retrieval_eval_runs`

## Finalidade
Guardar testes de recuperação por rodada.

### Campos recomendados
- `id` — UUID
- `ingestion_run_id` — FK
- `bloco_logico` — texto
- `query` — texto
- `tipo_teste` — `canonica`, `autoridade`, `contaminacao`, `atencao`
- `top_k_json` — json/jsonb
- `resultado` — `pass`, `warning`, `fail`
- `observacao` — texto nullable
- `created_at` — timestamp

### Objetivo
Sem isso, “pareceu bom” vira metodologia oficial. E isso é péssimo.

---

## Tabela 5 — `document_quarantine` (recomendada)

## Finalidade
Segurar documentos problemáticos fora do fluxo principal.

### Campos recomendados
- `id`
- `source_document_id`
- `motivo`
- `detalhes`
- `needs_review` — boolean
- `review_status` — `pendente`, `liberado`, `mantido_fora`
- `created_at`
- `reviewed_at`

---

## Enumerações recomendadas

## `ramo`
- `administrativo`
- `constitucional`
- `direitos_humanos`
- `internacional`
- `penal`
- `eleitoral`
- `eca`
- `educacao`
- `consumidor`

## `fonte_tipo`
- `lei`
- `legislacao_anotada`
- `resolucao`
- `decreto`
- `doutrina`
- `questao`
- `material_de_apoio`
- `convencao`
- `sumula`

## `autoridade`
- `planalto`
- `stf`
- `stj`
- `tse`
- `tcu`
- `conanda`
- `cnj`
- `cnmp`
- `onu`
- `oea`
- `oit`
- `banca`
- `material_proprio`
- `desconhecida`

## `peso_confianca`
- `alto`
- `medio`
- `baixo`

## `status_documento`
- `aprovado`
- `quarentena`
- `descartado`
- `revisao_manual`

---

## Regras de normalização de caminho

Todo documento deve ter:
- caminho original
- caminho normalizado
- pasta física de origem
- bloco lógico inferido

### Exemplo
Pasta física:
- `constitucional_direitos_humanos_internacional/`

Bloco lógico inferido:
- `constitucional`

### Regra
Nunca consultar só a pasta física quando o bloco lógico já tiver sido refinado.

---

## Regras de classificação inicial

A classificação deve acontecer em duas camadas:

1. **nível do documento**
2. **nível do chunk**

### Documento
Define:
- ramo base
- fonte_tipo
- autoridade
- peso_confianca

### Chunk
Herda isso e adiciona:
- `tem_atencao`
- `tipo_marcacao`
- `relevancia_estudo`
- `artigo_ref`
- `titulo_secao`
- ajuste de prioridade

---

## Regras iniciais de score/ranking

## Objetivo
Gerar uma `prioridade_recuperacao` inicial simples, estável e auditável.

### Modelo recomendado: score heurístico

Pontuação base por `peso_confianca`:
- `alto` = 100
- `medio` = 70
- `baixo` = 40

Ajuste por `fonte_tipo`:
- `lei` = +20
- `resolucao` = +18
- `decreto` = +15
- `convencao` = +15
- `legislacao_anotada` = +8
- `doutrina` = +5
- `material_de_apoio` = +2
- `questao` = -5
- `sumula` = +18

Ajuste por `autoridade`:
- `planalto` = +20
- `stf` = +20
- `stj` = +18
- `tse` = +18
- `tcu` = +12
- `cnj` = +10
- `cnmp` = +10
- `conanda` = +10
- `onu` = +12
- `oea` = +12
- `oit` = +10
- `banca` = -5
- `material_proprio` = -2
- `desconhecida` = -10

Ajuste por sinais didáticos:
- `tem_atencao = true` = +8
- `relevancia_estudo = alta` = +5
- `tem_anotacao = true` = +2

Ajuste por risco editorial:
- material excessivamente editorializado = -10
- origem pouco clara = -15
- chunk pobre/curto demais = -8

### Observação importante
Esse score **não substitui similaridade semântica**.
Ele serve como boost/reordenação inicial.

### Regra hierárquica
Se houver conflito entre:
- fonte oficial forte
- material anotado com `#Atenção`

a fonte oficial deve continuar na frente em condições normais.

---

## Pseudocódigo do pipeline

```python
def run_ingestion(bloco_logico, pasta_origem, run_key):
    run = create_ingestion_run(run_key, bloco_logico, pasta_origem)

    manifest = discover_files(pasta_origem)
    save_manifest(run, manifest)

    for file in manifest:
        doc = register_source_document(run, file)

        extracted = extract_text(file)
        update_extraction(doc, extracted)

        if extracted.status in ["falha"] or extracted.text_is_poor:
            move_to_quarantine(doc, motivo="extracao_ruim")
            continue

        classification = classify_document(doc, extracted.text)
        update_document_classification(doc, classification)

        if classification.is_ambiguous:
            mark_review(doc, motivo="classificacao_ambigua")
            continue

        signals = detect_didactic_signals(extracted.text)
        update_document_signals(doc, signals)

        chunks = chunk_document(doc, extracted.text)

        for i, chunk in enumerate(chunks):
            chunk_meta = enrich_chunk_metadata(doc, chunk, i)
            chunk_meta["prioridade_recuperacao"] = score_chunk(chunk_meta)
            save_chunk(run, doc, chunk_meta)

    generate_embeddings_for_run(run)

    eval_queries = get_eval_queries(bloco_logico)
    eval_results = evaluate_retrieval(run, eval_queries)
    save_eval_results(run, eval_results)

    decision = decide_run_status(eval_results)
    finalize_run(run, decision)

    return run
```

---

## Regras de chunking — especificação prática

### Estratégia principal
Usar chunking estrutural com fallback por tamanho.

### Ordem de preferência
1. detectar cabeçalhos legais (`Art.`, `§`, `Inciso`, `CAPÍTULO`, `SEÇÃO`)
2. quebrar por unidades temáticas
3. fallback por janela de caracteres/tokens com sobreposição leve

### Parâmetros iniciais sugeridos
- chunk alvo: 600 a 1200 tokens
- overlap leve: 80 a 150 tokens
- evitar quebrar artigo no meio quando possível

### Regras especiais
- documento legal puro: chunk por agrupamento de artigos coerentes
- resolução extensa: chunk por seção + artigos
- material comentado: separar comentário de texto-base quando a estrutura permitir
- questão comentada: manter enunciado + comentário principal, sem engolir o PDF inteiro num chunk só

---

## Regras de detecção de `#Atenção`

### Mínimo viável
Regex case-insensitive para:
- `#atenção`
- `#atencao`

### Saída
No chunk:
- `tem_atencao = true`
- `tipo_marcacao = "atencao"`
- `relevancia_estudo = "alta"`

No documento:
- `tem_atencao_documento = true` se ao menos um chunk tiver marcação

---

## Regras de quarentena

Documento vai para quarentena se ocorrer qualquer um destes casos:

1. extração vazia ou quase vazia
2. texto ilegível ou extremamente corrompido
3. classificação impossível com segurança mínima
4. duplicata problemática
5. material muito fraco ou sem utilidade clara

### Exemplo de motivo
- `extracao_ruim`
- `origem_duvidosa`
- `classificacao_ambigua`
- `duplicata`
- `editorializacao_excessiva`

---

## Regras de rollback

Cada `ingestion_run` deve poder ser revertida por `run_key`.

### Estratégia simples
Rollback lógico:
- marcar `ingestion_run.status = rolled_back`
- desativar chunks/documentos vinculados
- remover do índice vetorial ou marcá-los como inativos

### Regra
Nunca fazer rollback no escuro.
Sempre registrar:
- motivo
- responsável
- timestamp

---

## Formato de relatório operacional por ingestão

## Relatório resumido JSON

```json
{
  "run_key": "lote1_v1_eleitoral",
  "bloco_logico": "eleitoral",
  "arquivos_encontrados": 120,
  "arquivos_aprovados": 97,
  "arquivos_quarentena": 18,
  "arquivos_descartados": 5,
  "chunks_gerados": 1432,
  "chunks_com_atencao": 214,
  "top_autoridades": ["planalto", "tse"],
  "status_final": "validated"
}
```

## Relatório humano em markdown

```text
Run: lote1_v1_eleitoral
Bloco lógico: eleitoral
Status: validated

Arquivos encontrados: 120
Aprovados: 97
Quarentena: 18
Descartados: 5
Chunks gerados: 1432
Chunks com #Atenção: 214

Principais autoridades:
- planalto
- tse

Principais problemas:
- PDFs com extração parcial
- 6 arquivos com classificação ambígua
- 3 materiais de apoio com origem fraca

Decisão:
Aprovado para permanência no índice.
```

---

## Regras de avaliação de recuperação

## Critério mínimo por query
Para cada consulta de teste, registrar:
- top 10 retornados
- posição da fonte ideal
- posição da primeira fonte oficial
- presença de contaminação cruzada
- observação manual curta

### Heurística simples de aprovação
- `pass`: fonte ideal/topicamente correta aparece forte no topo
- `warning`: resultado aceitável, mas com ruído relevante
- `fail`: retorno incorreto, poluído ou com ranking incoerente

### Gate por bloco
Se houver muitos `fail`, o bloco não fecha.

---

## Ordem de implementação recomendada

### Etapa 1
Criar tabelas e enums.

### Etapa 2
Implementar descoberta de arquivos + manifesto.

### Etapa 3
Implementar extração de texto com status.

### Etapa 4
Implementar classificador documental inicial.

### Etapa 5
Implementar chunking estruturado.

### Etapa 6
Implementar enriquecimento + score heurístico.

### Etapa 7
Persistir chunks + embeddings.

### Etapa 8
Implementar suíte mínima de avaliação de recuperação.

### Etapa 9
Rodar primeiro bloco: `eleitoral`.

---

## Definition of Done do pipeline mínimo

O pipeline mínimo do Lote 1 só pode ser considerado pronto quando conseguir:

- ingerir `eleitoral` de ponta a ponta
- gerar manifesto, documentos e chunks
- detectar `#Atenção`
- calcular `prioridade_recuperacao`
- indexar embeddings
- executar testes de recuperação
- aprovar ou reprovar a run com rastreabilidade

Se não faz isso no eleitoral, ainda não está pronto para os blocos mais confusos.

---

## Conclusão

O Passo 5 transforma o plano em especificação real de implementação.

A espinha dorsal está definida:
- entidades
- campos
- enums
- regras
- score inicial
- pseudocódigo
- relatórios
- rollback

Agora já dá para alguém sentar e codar o pipeline com critério.
Sem isso, o risco é o clássico: engenharia improvisada, base poluída e depois todo mundo fingindo que o RAG “está meio estranho”.
