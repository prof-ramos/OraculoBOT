# Passo 2 — Classificação Operacional do Lote 1

## Objetivo

Definir a classificação operacional do **Lote 1** antes de qualquer ingestão no schema `juridico`, incorporando metadados mínimos, peso de confiança e tratamento especial para marcações do tipo **`#Atenção`**.

---

## Escopo do Lote 1

Pastas validadas para entrada prioritária:

- `administrativo/`
- `constitucional_direitos_humanos_internacional/`
- `penal/`
- `eleitoral/`
- `eca_e_educacao/`
- `consumidor/`

---

## Descoberta importante

Foi identificado que os documentos usam marcações explícitas do tipo:

- `#Atenção`
- eventualmente variações equivalentes (`#Atencao`)

Essas marcações aparecem dentro do corpo do material e sinalizam pontos considerados importantes para estudo ou cobrança.

### Implicação

Esses trechos **não podem ser ignorados**.
Eles devem gerar metadado específico e influenciar o peso do chunk na recuperação.

---

## Regra sobre `#Atenção`

### Interpretação

Trechos marcados com `#Atenção` serão tratados como:
- destaque didático
- potencial ponto de prova
- conteúdo de alta relevância para recuperação em contexto de estudo

### Metadado adicional obrigatório

Quando um chunk contiver `#Atenção` (ou variação equivalente), adicionar:

- `tem_atencao: true`
- `tipo_marcacao: atencao`
- `relevancia_estudo: alta`

Quando não houver:

- `tem_atencao: false`

### Regra de peso

- chunk com `#Atenção` → aumentar prioridade de recuperação
- isso **não transforma** o conteúdo em jurisprudência ou fonte oficial superior
- apenas sinaliza que é ponto didático relevante

Ou seja:
- melhora utilidade para prova
- não altera a hierarquia de autoridade da fonte

---

## Metadados mínimos obrigatórios

Todo chunk do Lote 1 deve receber, no mínimo:

- `ramo`
- `fonte_tipo`
- `autoridade`
- `arquivo_origem`
- `pasta_origem`
- `tem_anotacao`
- `tem_atencao`
- `peso_confianca`

### Metadados adicionais, quando disponíveis

- `ano`
- `banca`
- `subtema`
- `tipo`
- `relevancia_estudo`
- `tipo_marcacao`

---

## Taxonomia operacional por campo

### `ramo`

Valores iniciais esperados:
- `administrativo`
- `constitucional`
- `direitos_humanos`
- `internacional`
- `penal`
- `eleitoral`
- `eca`
- `educacao`
- `consumidor`

### Regra especial para pasta mista

Na pasta `constitucional_direitos_humanos_internacional/`, o ramo não deve ser herdado cegamente pelo nome da pasta.

Regra:
- se o documento for CF, ADI, ADC, ADPF, ação popular, CPI etc. → `constitucional`
- se for convenção/carta/comentário internacional de DH → `direitos_humanos` ou `internacional`
- se houver dúvida → marcar `subtema` e usar `peso_confianca = medio`

Na pasta `eca_e_educacao/`:
- ECA / infância / adolescência / SINASE / CONANDA → `eca`
- LDB / PNE / cotas / Fundeb / educação digital etc. → `educacao`

---

## Classificação por `fonte_tipo`

### Valores permitidos no Lote 1

- `lei`
- `legislacao_anotada`
- `resolucao`
- `decreto`
- `doutrina`
- `questao`
- `material_de_apoio`
- `convencao`
- `sumula` (fora do Lote 1 principal, mas já mapeada em pasta separada)

### Regras práticas

- arquivos de lei seca / código / estatuto / LC / MP → `lei`
- arquivos com grifos/anotações e estrutura didática → `legislacao_anotada`
- resoluções explícitas → `resolucao`
- decretos explícitos → `decreto`
- PDFs de comentários/enunciados → `doutrina` ou `material_de_apoio`
- materiais declarados como questões → `questao`
- convenções/cartas internacionais → `convencao`

---

## Classificação por `autoridade`

### Valores permitidos

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

### Regra prática

Usar a origem mais forte identificável no próprio nome/arquivo.

Exemplos:
- `cf_de_1988...` → `planalto`
- `res_23_607_de_2019` (TSE) → `tse`
- `res_105_de_2005_do_conanda` → `conanda`
- `convencao_americana_de_direitos_humanos...` → `oea`
- material de questões de concurso → `banca` ou `material_proprio`, conforme o caso

---

## Campo `tem_anotacao`

### Regras

- materiais declaradamente "grifados e anotados" → `true`
- lei/documento mais seco, sem sinal de intervenção didática → `false`

### Observação

No Lote 1, a tendência inicial é que muitos documentos da pasta principal recebam:
- `tem_anotacao = true`

Mas isso deve ser validado por amostragem por pasta.

---

## Campo `peso_confianca`

### Escala inicial

#### `alto`
Usar quando o material for:
- lei/código/estatuto oficial
- resolução claramente oficial
- decreto oficial
- convenção internacional estruturada e canônica

#### `medio`
Usar quando o material for:
- legislação anotada
- compilação didática confiável
- PDF de apoio com boa estrutura
- mistura de texto normativo e comentário

#### `baixo`
Usar quando o material for:
- questão comentada
- material heterogêneo
- anotação muito editorializada
- documento com origem/autoridade pouco clara

### Regra sobre `#Atenção`

`#Atenção` **não muda a autoridade da fonte**, mas pode elevar a prioridade de recuperação dentro da mesma faixa de confiança.

Exemplo:
- uma lei anotada continua `peso_confianca = medio`
- porém chunks com `tem_atencao = true` podem ganhar prioridade relativa sobre outros chunks médios

---

## Regras específicas por pasta do Lote 1

### 1. Administrativo

Classificação padrão:
- `ramo = administrativo`
- `fonte_tipo` conforme nome do arquivo
- `autoridade` em geral `planalto`, `cnj`, `tcu`, `agu`, etc.
- `peso_confianca = alto` para leis/decretos/resoluções oficiais
- `peso_confianca = medio` para enunciados/jornadas/material de apoio

### 2. Constitucional / Direitos Humanos / Internacional

Classificação deve ser refinada por documento:
- `constitucional` para CF, ações de controle, ação popular, CPI etc.
- `direitos_humanos` para tratados e sistemas protetivos
- `internacional` para DIP/DIPri e tratados gerais sem foco direto em DH

Regra extra:
- controlar peso e recuperação para evitar poluição em consultas puramente constitucionais

### 3. Penal

Classificação padrão:
- `ramo = penal`
- `fonte_tipo = lei` / `decreto` / `material_de_apoio`
- `peso_confianca = alto` para CP, leis penais especiais, estatutos
- `peso_confianca = medio` para PDFs de enunciados ou material de apoio

Observação:
- melhora cobertura penal normativa
- **não** substitui corpus jurisprudencial penal

### 4. Eleitoral

Classificação padrão:
- `ramo = eleitoral`
- `fonte_tipo = lei` / `resolucao`
- `autoridade = planalto` ou `tse`
- `peso_confianca = alto`

### 5. ECA / Educação

Separar dois ramos:
- `eca`
- `educacao`

Regra:
- CONANDA / SINASE / infância / juventude → `eca`
- LDB / PNE / Fundeb / cotas / bibliotecas / educação digital → `educacao`

### 6. Consumidor

Classificação padrão:
- `ramo = consumidor`
- `fonte_tipo = lei` / `decreto` / `material_de_apoio`
- `autoridade = planalto`, `senacon`, `aneel`, etc.
- `peso_confianca = alto` para normas oficiais
- `peso_confianca = medio` para notas técnicas e apoio

---

## Regra de validação antes de ingestão

Antes de ingerir qualquer pasta do Lote 1:

1. amostrar arquivos
2. verificar presença de anotação e `#Atenção`
3. confirmar `ramo`, `fonte_tipo`, `autoridade` e `peso_confianca`
4. só então iniciar ingestão do lote correspondente

---

## Saída esperada deste Passo 2

Ao final deste passo, o sistema deve ter:
- taxonomia operacional definida
- regra explícita para `#Atenção`
- critérios de confiança e classificação por pasta
- base pronta para começar a ingestão do Lote 1 com menor risco de poluição do RAG

---

## Próximo passo

**Passo 3**
- montar a estratégia de ingestão ramo por ramo do Lote 1
- começando pelo ramo de maior valor imediato
