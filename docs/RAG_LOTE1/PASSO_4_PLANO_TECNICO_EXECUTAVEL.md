# Passo 4 — Plano Técnico Executável de Ingestão do Lote 1

## Objetivo

Converter a estratégia operacional do Passo 3 em um **plano técnico de execução**, com pipeline, etapas objetivas, checkpoints, critérios de aceite e estrutura mínima para implementação da ingestão no schema `juridico`.

Este passo responde à pergunta prática:

**como colocar isso de pé sem improviso e sem enterrar o RAG em ruído?**

---

## Resultado esperado

Ao final deste passo, a equipe deve conseguir:

1. preparar arquivos para ingestão
2. extrair texto e metadados mínimos
3. identificar `#Atenção` e sinais de anotação
4. classificar cada documento/chunk
5. ingerir por bloco lógico controlado
6. validar recuperação antes de avançar

---

## Arquitetura lógica do pipeline

O pipeline do Lote 1 deve seguir esta sequência:

1. **descoberta de arquivos**
2. **normalização de caminho e nome**
3. **extração de texto**
4. **pré-classificação do documento**
5. **chunking estruturado**
6. **enriquecimento de metadados por chunk**
7. **pontuação de confiança e relevância**
8. **persistência no schema `juridico`**
9. **indexação vetorial**
10. **testes de recuperação**
11. **aprovação ou rollback da fase**

---

## Blocos lógicos de ingestão

Embora existam 6 pastas físicas, o plano deve operar com **9 blocos lógicos**:

1. `eleitoral`
2. `administrativo`
3. `penal`
4. `consumidor`
5. `eca`
6. `educacao`
7. `constitucional`
8. `direitos_humanos`
9. `internacional`

Essa separação não é frescura. É o que impede o sistema de misturar alhos jurídicos com bugalhos semânticos.

---

## Fase 0 — Preparação do ambiente

Antes de qualquer ingestão, preparar quatro coisas:

### 0.1. Manifesto de arquivos
Gerar uma listagem única dos documentos do Lote 1 contendo, no mínimo:
- caminho absoluto
- pasta de origem
- nome do arquivo
- extensão
- tamanho
- hash do arquivo

### 0.2. Área de staging
Criar uma camada intermediária de staging para não ingerir direto da pasta bruta.

Estrutura sugerida:

```text
/tmp/OraculoBOT/staging/lote1/
  manifest.csv
  raw_text/
  normalized/
  samples/
  logs/
  reports/
```

### 0.3. Registro de execução
Cada fase precisa gerar log próprio com:
- data/hora
- lote
- ramo/bloco lógico
- quantidade de arquivos processados
- quantidade de chunks gerados
- erros
- arquivos descartados

### 0.4. ID de versão da ingestão
Toda rodada deve ter um identificador, por exemplo:
- `lote1_v1_eleitoral`
- `lote1_v1_administrativo`

Sem versionamento, rollback vira loteria.

---

## Fase 1 — Descoberta e inventário de arquivos

### Objetivo
Mapear todos os documentos disponíveis antes de processar qualquer um.

### Entradas
Pastas do Lote 1:
- `administrativo/`
- `constitucional_direitos_humanos_internacional/`
- `penal/`
- `eleitoral/`
- `eca_e_educacao/`
- `consumidor/`

### Saída esperada
Um manifesto com colunas como:
- `documento_id`
- `arquivo_origem`
- `pasta_origem`
- `nome_arquivo`
- `ext`
- `tamanho_bytes`
- `hash_sha256`
- `status_inicial`

### Regras
- deduplicar por hash quando necessário
- arquivos corrompidos ou ilegíveis devem ser marcados, não ignorados silenciosamente
- nada de ingestão nesta fase

---

## Fase 2 — Extração de texto

### Objetivo
Transformar os documentos em texto utilizável sem perder referência de origem.

### Saída esperada por documento
- texto extraído bruto
- status de extração
- método de extração usado
- quantidade de caracteres

### Campos mínimos adicionais
- `extracao_status`: `ok`, `parcial`, `falha`
- `extracao_metodo`: ex. `pdf_text`, `ocr`, `docx`, `txt`

### Regras
- se a extração vier vazia ou muito pobre, o documento vai para revisão
- se o PDF for imagem e exigir OCR, isso deve ficar registrado
- texto bruto deve ficar rastreável ao arquivo original

### Critério de descarte temporário
Documento com texto insuficiente ou lixo excessivo:
- não entra automaticamente
- vai para fila de revisão

---

## Fase 3 — Pré-classificação documental

### Objetivo
Classificar cada documento antes do chunking.

### Campos a preencher no nível do documento
- `ramo`
- `fonte_tipo`
- `autoridade`
- `arquivo_origem`
- `pasta_origem`
- `tem_anotacao`
- `peso_confianca`
- `ano` (se possível)
- `banca` (se aplicável)
- `subtema` (se possível)
- `tipo` (se aplicável)

### Regras de classificação
Aplicar as regras do Passo 2 e a ordem do Passo 3.

### Regra crítica
Nas pastas mistas:
- classificar no nível do documento antes de qualquer chunk
- nunca herdar ramo só pelo nome da pasta

### Critério de dúvida
Se a classificação for ambígua:
- marcar `peso_confianca = medio`
- preencher `subtema`
- enviar para amostragem manual antes da ingestão

---

## Fase 4 — Detecção de sinais didáticos

### Objetivo
Marcar presença de anotação e destaque relevante para estudo.

### Detectar no mínimo
- `#Atenção`
- `#Atencao`
- outras variações simples previsíveis

### Campos obrigatórios
No nível do documento:
- `tem_atencao_documento`
- `tem_anotacao`

No nível do chunk:
- `tem_atencao`
- `tipo_marcacao`
- `relevancia_estudo`

### Regra
- presença de `#Atenção` em um trecho relevante do chunk → `tem_atencao = true`
- ausência → `tem_atencao = false`

### Observação técnica
A detecção deve ser simples e auditável.
Não inventa NLP sofisticado aqui de cara. Regex bem feita resolve o primeiro round.

---

## Fase 5 — Chunking estruturado

### Objetivo
Quebrar o texto em unidades úteis para recuperação.

### Regra geral
O chunking deve respeitar a estrutura jurídica quando possível.

### Prioridade estrutural
1. artigo
2. parágrafo
3. inciso/alínea
4. bloco temático curto
5. seção ou subtítulo

### Evitar
- chunks gigantes misturando múltiplos assuntos
- chunks minúsculos sem contexto
- quebra cega por número fixo de caracteres quando houver estrutura legal evidente

### Campos sugeridos por chunk
- `chunk_id`
- `documento_id`
- `ordem_chunk`
- `texto_chunk`
- `titulo_secao` (se houver)
- `artigo_ref` (se houver)
- `ramo`
- `fonte_tipo`
- `autoridade`
- `arquivo_origem`
- `pasta_origem`
- `tem_anotacao`
- `tem_atencao`
- `tipo_marcacao`
- `relevancia_estudo`
- `peso_confianca`
- `subtema`

### Regra para material comentado
Se o documento alterna texto normativo e comentário:
- tentar não fundir tudo no mesmo chunk
- separar núcleo normativo de comentário quando a estrutura permitir

Isso melhora muito a recuperação. Misturar tudo é pedir resposta confusa.

---

## Fase 6 — Enriquecimento e score operacional

### Objetivo
Aplicar metadados finais de ranking e controle.

### Campos operacionais recomendados
Além dos campos do Passo 2, adicionar:
- `versao_ingestao`
- `bloco_logico`
- `prioridade_recuperacao`
- `status_validacao`

### Regra de prioridade de recuperação
Modelo inicial sugerido:

- base pela `autoridade` + `fonte_tipo` + `peso_confianca`
- ajuste positivo para `tem_atencao = true`
- ajuste negativo para material muito editorializado ou pouco claro

### Exemplo de lógica qualitativa
- lei oficial + confiança alta → prioridade alta
- resolução oficial + confiança alta → prioridade alta
- legislação anotada + `#Atenção` → prioridade média-alta
- questão comentada → prioridade baixa ou média-baixa

### Importante
`#Atenção` melhora prioridade relativa.
Não vira passe VIP para passar na frente de fonte superior.

---

## Fase 7 — Persistência no schema `juridico`

### Objetivo
Salvar documento e chunks de forma rastreável e reversível.

### Requisito mínimo
Cada chunk precisa manter ligação com:
- documento original
- arquivo de origem
- versão da ingestão
- bloco lógico

### Recomendação de entidades
No mínimo, pensar em duas camadas:

1. **documentos**
   - metadados no nível do arquivo

2. **chunks**
   - texto indexável + metadados herdados e específicos

### Regras
- não sobrescrever silenciosamente chunks antigos
- preferir `upsert` versionado ou inserção com marca de versão
- permitir rollback por `versao_ingestao`

Se isso não existir, qualquer erro vira trabalho braçal de limpeza.

---

## Fase 8 — Indexação vetorial

### Objetivo
Gerar embeddings e preparar recuperação híbrida ou vetorial.

### Regras mínimas
- indexar por chunk, não por documento inteiro
- preservar metadados consultáveis
- garantir filtro por `ramo`, `fonte_tipo`, `autoridade`, `bloco_logico`

### Recomendação forte
A busca precisa conseguir filtrar por metadados.
Sem isso, quando entrar constitucional misturado com internacional, vai dar ruim.

---

## Fase 9 — Testes de recuperação

### Objetivo
Medir se a ingestão melhorou ou piorou o sistema.

### Tipos de teste

#### 1. Teste por consulta canônica
Rodar consultas jurídicas esperadas por ramo.

#### 2. Teste de autoridade
Verificar se fonte melhor aparece acima de fonte pior.

#### 3. Teste de contaminação cruzada
Verificar se um ramo está invadindo outro.

#### 4. Teste de destaque didático
Verificar se `#Atenção` ajuda sem romper a hierarquia documental.

---

## Consultas mínimas por bloco

### Eleitoral
- inelegibilidade reflexa
- propaganda eleitoral antecipada
- prestação de contas partidária
- registro de candidatura

### Administrativo
- poder de polícia
- improbidade administrativa
- processo administrativo disciplinar
- licitação dispensável

### Penal
- arrependimento posterior
- concurso material
- crime funcional
- legítima defesa putativa

### Consumidor
- fato do produto
- vício do serviço
- publicidade abusiva
- inversão do ônus da prova

### ECA
- medida socioeducativa em meio aberto
- conselho tutelar
- ato infracional
- adoção intuitu personae

### Educação
- Fundeb
- cotas raciais
- gestão democrática do ensino
- direito público subjetivo à educação

### Constitucional
- ADPF
- ação popular
- controle concentrado
- direitos fundamentais sociais

### Direitos Humanos
- controle de convencionalidade
- Convenção Americana
- Corte Interamericana
- dever estatal de proteção

### Internacional
- internalização de tratados
- costume internacional
- conflito entre tratado e lei interna
- responsabilidade internacional do Estado

---

## Critérios de aceite por fase

Uma fase só fecha se cumprir todos estes itens:

1. taxa aceitável de extração
2. classificação consistente por amostragem
3. metadados obrigatórios completos
4. detecção de `#Atenção` funcional
5. ranking sem inversão grotesca de autoridade
6. baixa contaminação semântica cruzada
7. capacidade de rollback preservada

Se não cumpriu, não “segue e vê depois”.
Volta e corrige.

---

## Amostragem mínima recomendada

Antes de liberar um bloco lógico inteiro:

- amostrar pelo menos 10 documentos ou 10% do bloco, o que for maior
- revisar manualmente os casos ambíguos
- registrar os erros de classificação mais frequentes

### Objetivo da amostragem
Encontrar cedo:
- metadado errado
- chunk ruim
- autoridade mal inferida
- ramo mal separado

---

## Política de exclusão e quarentena

Nem todo documento deve entrar direto no schema `juridico`.

### Mandar para quarentena quando houver:
- extração ruim
- origem incerta
- classificação ambígua demais
- material editorializado sem valor claro
- duplicata suspeita

### Status sugeridos
- `aprovado`
- `quarentena`
- `descartado`
- `revisao_manual`

Essa camada evita contaminar a base principal com tralha jurídica.

---

## Ordem prática de execução

### Sprint 1 — Eleitoral
Entregas:
- manifesto do ramo
- extração validada
- regras finais de chunking
- ingestão do bloco `eleitoral`
- bateria de testes
- relatório de aprovação

### Sprint 2 — Administrativo
Entregas equivalentes, ajustando regras conforme aprendizado do Sprint 1.

### Sprint 3 — Penal
Mesmo padrão.

### Sprint 4 — Consumidor
Mesmo padrão.

### Sprint 5 — ECA + Educação
Executar como dois blocos lógicos distintos.

### Sprint 6 — Constitucional + Direitos Humanos + Internacional
Executar de forma separada e conservadora.

---

## Artefatos obrigatórios por sprint

Cada sprint deve produzir, **para cada bloco lógico incluído na sprint**:

1. manifesto de arquivos do bloco
2. relatório de amostragem
3. relatório de erros de extração
4. relatório de classificação
5. relatório de testes de recuperação
6. decisão final do bloco: `aprovado`, `ajustar`, `rollback`

Se uma sprint contiver múltiplos blocos lógicos (como `eca` + `educacao`, ou `constitucional` + `direitos_humanos` + `internacional`), **cada bloco deve ter seu próprio `run_key`, seu próprio conjunto de relatórios e sua própria decisão final**. Não existe aprovação única da sprint inteira nesses casos.

---

## Estrutura mínima de relatório por bloco

Modelo sugerido:

```text
Bloco lógico: eleitoral
Versão da ingestão: lote1_v1_eleitoral
Arquivos encontrados: X
Arquivos aprovados: Y
Arquivos em quarentena: Z
Chunks gerados: N
#Atenção detectado em: K chunks
Principais autoridades: planalto, tse
Principais erros: ...
Consultas testadas: ...
Status final: aprovado
```

---

## Checklist executivo

Antes de ingerir um bloco:
- [ ] manifesto gerado
- [ ] texto extraído
- [ ] amostragem feita
- [ ] ramo confirmado
- [ ] fonte_tipo confirmado
- [ ] autoridade confirmada
- [ ] regra de chunking validada
- [ ] `#Atenção` detectável
- [ ] versionamento definido

Depois da ingestão:
- [ ] embeddings gerados
- [ ] filtros por metadado funcionando
- [ ] consultas de teste rodadas
- [ ] ranking validado
- [ ] contaminação cruzada verificada
- [ ] relatório final emitido

---

## Conclusão técnica

O Passo 4 fecha a ponte entre ideia e execução.

A implementação correta do Lote 1 não é “subir PDF no vetor e rezar”.
É:
- classificar bem
- chunkar direito
- preservar autoridade
- testar recuperação
- avançar por blocos pequenos

A ordem recomendada continua sendo:
1. eleitoral
2. administrativo
3. penal
4. consumidor
5. eca
6. educacao
7. constitucional
8. direitos_humanos
9. internacional

Se seguirem isso, dá para construir um RAG útil.
Se pularem controles, vira um cemitério semântico com embedding bonito em cima.
