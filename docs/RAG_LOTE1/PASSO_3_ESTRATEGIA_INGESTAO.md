# Passo 3 — Estratégia de Ingestão do Lote 1

## Objetivo

Transformar a classificação operacional definida no Passo 2 em uma **ordem concreta de ingestão**, com critérios por ramo, prioridades de execução, controles de qualidade e regras para reduzir poluição do schema `juridico`.

---

## Princípio central

O Lote 1 **não deve ser ingerido em massa de forma cega**.
A estratégia correta é:

1. priorizar o ramo de maior valor imediato
2. ingerir por blocos temáticos controlados
3. validar recuperação antes de ampliar o lote
4. preservar separação entre material normativo forte e material didático/anotado

Ou seja: **menos volume, mais controle**.

---

## Critério de priorização do Lote 1

A ordem de ingestão deve considerar quatro fatores:

1. **valor imediato para resposta**
   - probabilidade de aparecer em consultas reais
   - impacto na utilidade do RAG

2. **clareza classificatória**
   - menor ambiguidade de `ramo`, `fonte_tipo`, `autoridade`
   - menor risco de erro semântico

3. **força documental**
   - predominância de normas oficiais, resoluções ou convenções canônicas
   - menor peso de material excessivamente editorializado

4. **risco de poluição de recuperação**
   - chance de um ramo “invadir” consultas de outro
   - chance de material anotado ou heterogêneo aparecer acima de fonte melhor

---

## Ordem recomendada de ingestão

### Ordem geral

1. `eleitoral/`
2. `administrativo/`
3. `penal/`
4. `consumidor/`
5. `eca_e_educacao/`
6. `constitucional_direitos_humanos_internacional/`

---

## Justificativa da ordem

### 1. Eleitoral — começar aqui

**Motivo:**
- alta densidade normativa
- autoridade forte e clara (`planalto`, `tse`)
- baixa ambiguidade classificatória
- excelente ganho prático com baixo risco

**Perfil esperado:**
- leis eleitorais
- resoluções TSE
- material normativo relativamente limpo

**Risco:** baixo
**Valor imediato:** alto

**Decisão:** este deve ser o **primeiro ramo ingerido**.

---

### 2. Administrativo

**Motivo:**
- muito útil para consultas recorrentes
- forte presença de leis, decretos, resoluções e atos oficiais
- boa relação entre utilidade e previsibilidade

**Risco principal:**
- mistura de material oficial com apoio/enunciados/jornadas

**Controle necessário:**
- separar bem `lei` / `decreto` / `resolucao` de `material_de_apoio`

**Risco:** médio-baixo
**Valor imediato:** alto

---

### 3. Penal

**Motivo:**
- boa utilidade normativa
- classificação razoavelmente estável
- leis penais especiais e código penal tendem a performar bem

**Limite importante:**
- não fingir que isso cobre jurisprudência penal
- evitar overclaim de cobertura

**Risco:** médio
**Valor imediato:** alto

---

### 4. Consumidor

**Motivo:**
- tende a ter normas e materiais utilizáveis
- escopo menos explosivo que constitucional
- boa utilidade prática

**Risco principal:**
- mistura de norma com material institucional de apoio

**Risco:** médio
**Valor imediato:** médio-alto

---

### 5. ECA / Educação

**Motivo:**
- útil, mas é uma pasta naturalmente híbrida
- exige separação semântica real entre `eca` e `educacao`

**Risco principal:**
- contaminação entre infância/adolescência e política educacional

**Risco:** médio-alto
**Valor imediato:** médio

---

### 6. Constitucional / Direitos Humanos / Internacional — deixar por último

**Motivo:**
- é o ramo com maior risco de confusão semântica
- pasta mista
- maior chance de poluir recuperação se entrar cedo demais
- exige critério fino para evitar que tratados, comentários e materiais híbridos invadam consultas estritamente constitucionais

**Risco:** alto
**Valor imediato:** alto, mas com alto potencial de dano se mal ingerido

**Decisão:** ingerir só depois de validar bem os ramos anteriores.

---

## Estratégia operacional de ingestão

A ingestão deve ocorrer em **6 fases**, uma por ramo/pasta, com gate de validação entre elas.

### Regra geral por fase

Cada fase deve seguir este fluxo:

1. amostragem dos arquivos da pasta
2. validação manual dos padrões reais da pasta
3. definição das regras finais daquele ramo
4. ingestão controlada
5. teste de recuperação
6. só então liberar a fase seguinte

Se a fase falhar em qualidade de recuperação, **não avança**.

---

## Fase 1 — Eleitoral

### Objetivo
Subir o primeiro bloco com máxima previsibilidade e baixo ruído.

### Escopo preferencial
Priorizar nesta ordem:
1. leis eleitorais oficiais
2. código eleitoral
3. lei das eleições
4. lei dos partidos políticos
5. resoluções TSE estruturantes
6. só depois materiais anotados correlatos

### Critérios de ingestão
- `fonte_tipo = lei` ou `resolucao` entram primeiro
- `autoridade = planalto` ou `tse`
- `peso_confianca = alto` para material oficial
- materiais anotados entram só em segunda leva

### Regras de chunk prioritárias
- preservar artigos, incisos, parágrafos e ementas quando houver
- evitar chunk excessivamente longo em resolução normativa densa
- marcar `tem_atencao` quando houver destaque didático

### Testes mínimos após ingestão
Executar consultas de validação como:
- inelegibilidade
- propaganda eleitoral
- registro de candidatura
- prestação de contas
- federação partidária

### Critério de aprovação
A recuperação deve retornar:
- norma correta no topo ou muito perto do topo
- resolução TSE relevante sem afogamento por material editorial
- chunks com `#Atenção` melhor posicionados entre materiais da mesma faixa

---

## Fase 2 — Administrativo

### Objetivo
Ampliar cobertura com base normativa forte e alta utilidade prática.

### Ordem interna recomendada
1. leis e decretos estruturantes
2. improbidade, processo administrativo, licitações, agentes públicos etc.
3. resoluções e atos normativos relevantes
4. jornadas, enunciados, materiais de apoio

### Critérios de ingestão
- oficiais primeiro
- enunciados e apoio só depois
- materiais muito comentados devem entrar com `peso_confianca = medio`

### Atenção especial
Administrativo costuma misturar:
- norma
- interpretação institucional
- apoio doutrinário

Isso exige segurar a mão: se entrar tudo de uma vez, o RAG vira bagunça.

### Testes mínimos
- poder de polícia
- licitação
- processo administrativo
- improbidade
- responsabilidade civil do Estado

---

## Fase 3 — Penal

### Objetivo
Adicionar cobertura legal penal sem vender falsa completude jurisprudencial.

### Ordem interna recomendada
1. Código Penal
2. leis penais especiais
3. estatutos penais correlatos
4. material de apoio e enunciados

### Critérios de ingestão
- lei seca e legislação oficial primeiro
- material comentado depois
- qualquer material excessivamente resumido ou esquemático entra com cautela

### Testes mínimos
- concurso de pessoas
- arrependimento posterior
- crimes contra a administração pública
- legítima defesa
- lei de drogas

### Critério de segurança
Se consultas abertas começarem a puxar resumos pobres acima de norma forte, a fase precisa revisão.

---

## Fase 4 — Consumidor

### Objetivo
Subir conteúdo útil e relativamente bem delimitado.

### Ordem interna recomendada
1. CDC e decretos nucleares
2. normas complementares relevantes
3. atos institucionais e materiais de apoio

### Critérios de ingestão
- norma forte primeiro
- apoio institucional depois
- material pouco identificável entra com `peso_confianca = baixo` ou fica fora

### Testes mínimos
- vício do produto
- fato do produto
- inversão do ônus da prova
- publicidade enganosa
- cadastro de inadimplentes

---

## Fase 5 — ECA / Educação

### Objetivo
Ingerir pasta híbrida com separação forte de ramo.

### Regra central
Não ingerir essa pasta como bloco único lógico.
Ela deve ser tratada como **dois sub-ramos independentes**:
- `eca`
- `educacao`

### Ordem interna recomendada
1. ECA e normas de infância/adolescência
2. SINASE / CONANDA / atos correlatos
3. LDB / PNE / Fundeb / cotas / educação digital
4. materiais de apoio e anotados

### Critério crítico
Antes da ingestão completa, amostrar para validar se:
- infância/adolescência está bem destacada
- educação não está sendo confundida com proteção integral

### Testes mínimos
Para `eca`:
- ato infracional
- medida socioeducativa
- conselho tutelar
- adoção

Para `educacao`:
- direito à educação
- LDB
- Fundeb
- cotas

---

## Fase 6 — Constitucional / Direitos Humanos / Internacional

### Objetivo
Ingerir o ramo mais sensível só depois de o pipeline estar confiável.

### Regra central
Essa pasta deve ser tratada como **pasta mista com triagem fina**, não como ramo único.

### Subdivisão operacional obrigatória
Separar logicamente em três grupos:
1. `constitucional`
2. `direitos_humanos`
3. `internacional`

### Ordem interna recomendada
1. Constituição Federal e materiais normativos nitidamente constitucionais
2. controle de constitucionalidade, remédios constitucionais, ações constitucionais
3. convenções e cartas de direitos humanos
4. tratados e materiais internacionais gerais
5. materiais comentados e híbridos por último

### Riscos a controlar
- consulta constitucional puxando tratado internacional irrelevante
- consulta de direitos humanos puxando comentário doutrinário fraco acima de fonte forte
- internacional geral contaminando questões constitucionais nacionais

### Testes mínimos
Para `constitucional`:
- controle concentrado
- ação popular
- CPI
- direitos fundamentais

Para `direitos_humanos`:
- Convenção Americana
- sistema interamericano
- controle de convencionalidade

Para `internacional`:
- tratados
- incorporação
- conflito entre norma interna e internacional

### Critério de entrada
Se a recuperação cruzada ficar poluída, esse ramo deve ser refinado antes de ir para produção.

---

## Regras transversais de ingestão

## 1. Oficial antes de anotado

Sempre que houver material oficial e material anotado sobre o mesmo núcleo temático:
- ingerir oficial primeiro
- anotado depois

Isso evita que o sistema aprenda a responder pela margem em vez do texto-base.

---

## 2. `#Atenção` melhora ranking relativo, não autoridade

Chunks com `tem_atencao = true`:
- podem subir dentro da mesma faixa temática
- não devem atropelar fonte oficial mais forte só porque foram destacados

Resumo:
- destaque didático ajuda
- não pode corromper hierarquia documental

---

## 3. Material muito heterogêneo pode ficar de fora

Nem tudo precisa entrar.
Se o arquivo tiver:
- origem pouco clara
- estrutura ruim
- excesso de comentário sem fonte
- baixa utilidade semântica

então a decisão correta pode ser **não ingerir**.

Isso é maturidade, não omissão.

---

## 4. Recuperação vale mais que volume

Critério de sucesso não é “quantos PDFs subiram”.
Critério de sucesso é:
- recuperar melhor
- com menos ruído
- com autoridade coerente

Se dobrar o volume e piorar a resposta, foi uma ingestão ruim. Simples.

---

## Critérios de aprovação por fase

Cada fase só pode ser considerada concluída se atender aos seguintes pontos:

1. metadados consistentes por amostragem
2. `tem_atencao` detectado corretamente quando aplicável
3. consultas de teste retornando documentos esperados
4. ausência de poluição grave por material fraco
5. autoridade da fonte preservada no ranking

Se qualquer item falhar, a fase volta para ajuste.

---

## Saída esperada do Passo 3

Ao final deste passo, deve ficar definida a seguinte estratégia executiva:

- **primeiro ramo a ingerir:** `eleitoral`
- **ordem completa:**
  1. eleitoral
  2. administrativo
  3. penal
  4. consumidor
  5. eca
  6. educacao
  7. constitucional
  8. direitos_humanos
  9. internacional

Observação:
Embora o Lote 1 tenha 6 pastas físicas, operacionalmente ele deve virar **9 blocos lógicos de ingestão**, porque as pastas mistas precisam ser quebradas.

---

## Conclusão operacional

O Passo 2 resolveu **como classificar**.
O Passo 3 resolve **como ingerir sem estragar o RAG**.

A decisão correta é começar por **eleitoral**, avançar para ramos normativamente fortes e deixar por último o material com maior ambiguidade semântica.

Se fizer isso com disciplina, o RAG melhora.
Se tentar subir tudo de uma vez, vira lama.
