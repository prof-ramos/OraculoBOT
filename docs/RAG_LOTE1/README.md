# RAG Lote 1 — Guia Mestre para LLMs e Implementadores

## Objetivo

Esta pasta reúne a documentação operacional do **pipeline de ingestão do Lote 1** do RAG jurídico.

Se você é uma LLM, agente de código ou desenvolvedor entrando nesse repositório para continuar o trabalho, **comece por aqui**.

---

## Ordem de leitura obrigatória

Leia nesta ordem:

1. `PASSO_2_CLASSIFICACAO_OPERACIONAL.md`
2. `PASSO_3_ESTRATEGIA_INGESTAO.md`
3. `PASSO_4_PLANO_TECNICO_EXECUTAVEL.md`
4. `PASSO_5_ESPECIFICACAO_IMPLEMENTACAO.md`

Essa ordem não é decorativa.
Ela vai de:
- **como classificar**
- para **como priorizar**
- para **como executar**
- para **como implementar**

---

## Resumo executivo

### O que é o Lote 1
Conjunto inicial de pastas jurídicas priorizadas para ingestão controlada no schema `juridico`.

Pastas físicas do Lote 1:
- `administrativo/`
- `constitucional_direitos_humanos_internacional/`
- `penal/`
- `eleitoral/`
- `eca_e_educacao/`
- `consumidor/`

### Blocos lógicos reais
Apesar de existirem 6 pastas físicas, a ingestão deve operar em **9 blocos lógicos**:
- `eleitoral`
- `administrativo`
- `penal`
- `consumidor`
- `eca`
- `educacao`
- `constitucional`
- `direitos_humanos`
- `internacional`

---

## Ordem oficial de ingestão

Siga esta ordem:

1. `eleitoral`
2. `administrativo`
3. `penal`
4. `consumidor`
5. `eca`
6. `educacao`
7. `constitucional`
8. `direitos_humanos`
9. `internacional`

### Por quê?
Porque começar por pasta mista e semanticamente confusa é pedir para estragar o RAG cedo.

---

## Regras imutáveis

### 1. Não ingerir tudo de uma vez
Ingestão em massa sem validação é proibida.

### 2. Material oficial vem antes de material anotado
Lei, decreto, resolução e convenção forte têm precedência operacional.

### 3. `#Atenção` melhora ranking relativo, não autoridade
Não pode passar material fraco na frente de fonte forte só porque tem destaque didático.

### 4. Pasta física não define ramo sozinha
Especialmente nas pastas:
- `constitucional_direitos_humanos_internacional/`
- `eca_e_educacao/`

### 5. Documento ruim vai para quarentena
Não inventar ingestão heróica de material lixo.

### 6. Cada rodada precisa de versionamento
Use `run_key` claro, por exemplo:
- `lote1_v1_eleitoral`
- `lote1_v1_administrativo`

### 7. Toda fase precisa de teste de recuperação
Sem teste, não existe “fase concluída”.

---

## O que uma LLM deve fazer ao continuar este trabalho

### Se a tarefa for conceitual/documental
- respeitar a taxonomia do Passo 2
- respeitar a ordem de ingestão do Passo 3
- respeitar o pipeline do Passo 4
- respeitar o schema lógico do Passo 5

### Se a tarefa for de implementação
Antes de codar:
1. confirmar qual bloco lógico está sendo implementado
2. confirmar se há `run_key` definido
3. confirmar se a saída precisa persistir em `juridico`
4. confirmar se existe camada de quarentena e rollback

### Se a tarefa for de refatoração
- não remover rastreabilidade
- não colapsar documento e chunk numa entidade só se isso perder auditoria
- não trocar critérios explícitos por heurística obscura sem justificar

### Se a tarefa for de avaliação
- usar consultas canônicas por ramo
- verificar autoridade
- medir contaminação cruzada
- registrar resultado por rodada

---

## Definition of Done mínima

O pipeline do Lote 1 só pode ser considerado funcional quando conseguir, no mínimo, para o bloco `eleitoral`:

- descobrir arquivos
- extrair texto com status
- classificar documento
- detectar `#Atenção`
- gerar chunks com metadados
- calcular prioridade de recuperação
- persistir com versionamento
- indexar embeddings
- rodar testes de recuperação
- aprovar ou reprovar a rodada

Se ainda não faz isso em `eleitoral`, não está pronto para os blocos mistos.

---

## Próximo passo recomendado para implementação

Se esta documentação já estiver pronta e a implementação ainda não tiver começado, a sequência correta é:

1. criar as tabelas/entidades descritas no Passo 5
2. implementar descoberta de arquivos + manifesto
3. implementar extração de texto
4. implementar classificação documental
5. implementar chunking estruturado
6. implementar score heurístico inicial
7. indexar embeddings
8. criar suíte mínima de avaliação
9. rodar `eleitoral`

---

## Arquivos desta pasta

- `PASSO_2_CLASSIFICACAO_OPERACIONAL.md`
- `PASSO_3_ESTRATEGIA_INGESTAO.md`
- `PASSO_4_PLANO_TECNICO_EXECUTAVEL.md`
- `PASSO_5_ESPECIFICACAO_IMPLEMENTACAO.md`

---

## Regra final

Se houver conflito entre improviso e esta documentação, a documentação vence — a menos que seja atualizada explicitamente.

Improvisar em pipeline jurídico com RAG é a rota mais curta para uma base bonita e burra.
