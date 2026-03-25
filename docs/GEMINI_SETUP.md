# Configurar Gemini API para RAG

## Por que usar Gemini?

- ✅ **Free-tier generoso** até 1.500 requisições/dia
- ✅ **Embeddings de alta qualidade** (768 dimensões)
- ✅ **Sem custos** para desenvolvimento/testes
- ✅ **Alternativa gratuita** ao OpenAI

## Passo a Passo

### 1. Obter API Key

1. Acesse: https://ai.google.dev/
2. Clique em **"Get API Key"** (ou "Criar chave API")
3. Faça login com sua conta Google
4. Crie um novo projeto (ou use existente)
5. Copie a API key gerada

### 2. Configurar no OraculoBOT

Edite o arquivo `.env`:

```bash
GEMINI_API_KEY=AIzaSy...sua-chave-aqui
```

### 3. Verificar Instalação

```bash
# Verificar se pacote está instalado
uv run python -c "import google.generativeai as genai; print('✅ Gemini instalado')"

# Testar embedding (opcional - requer API key)
uv run python -c "
from agno.knowledge.embedder.google import GeminiEmbedder
import os
key = os.getenv('GEMINI_API_KEY')
if key:
    embedder = GeminiEmbedder(api_key=key)
    emb = embedder.get_embedding('Teste de embedding')
    print(f'✅ Embedding Gemini: {len(emb)} dimensões')
else:
    print('⚠️  GEMINI_API_KEY não configurada')
"
```

## Diferenças: OpenAI vs Gemini

| Característica | OpenAI | Gemini |
|----------------|--------|---------|
| Modelo | text-embedding-3-small | text-embedding-004 |
| Dimensões | 1536 | 768 |
| Free-tier | Não | 1.500 req/dia |
| Custo | ~$0.02/1M tokens | Grátis (até limite) |
| Qualidade | Excelente | Excelente |

## Uso no Código

O código está configurado para usar **Gemini por padrão**:

```python
# oraculo_bot/rag.py
from agno.knowledge.embedder.google import GeminiEmbedder

_embedding_model = GeminiEmbedder(
    api_key=GEMINI_API_KEY,
    id="text-embedding-004",
    dimensions=768
)
```

## Testar RAG com Gemini

```bash
# Teste completo
uv run test_rag_simulated_message.py
```

Saída esperada:
```
✅ RAG: modelo de embeddings Gemini inicializado
✅ Contexto RAG recuperado
   - Similaridade: 85-95%
   - Conteúdo relevante para a query
```

## Troubleshooting

### Erro: "API key not valid"

**Solução**: Verificar se a GEMINI_API_KEY está correta no `.env`

### Erro: "quota exceeded"

**Causa**: Limite de 1.500 requisições/dia atingido

**Solução**:
- Aguardar reset (diário)
- Ou usar OPENAI_API_KEY como alternativa

### Erro: "No module named 'google.generativeai'"

**Solução**:
```bash
uv sync
```

## Limites e Cotas

**Free-tier Gemini:**
- 1.500 requisições/dia
- 15 requisições/minuto (rate limit)
- 768 dimensões por embedding

**Para produção:**
- Considerar plano pago do Gemini
- Ou usar OpenAI (custo menor em alta escala)

## Próximos Passos

1. ✅ Adicionar GEMINI_API_KEY ao `.env`
2. ✅ Testar com `uv run test_rag_simulated_message.py`
3. ✅ Iniciar bot: `uv run python -m oraculo_bot`
4. ✅ Enviar mensagem no Discord para testar

## Links Úteis

- [Google AI Studio](https://ai.google.dev/)
- [Documentação Gemini API](https://ai.google.dev/docs)
- [Preços e Cotas](https://ai.google.dev/pricing)
- [Agno GeminiEmbedder](https://docs.agno.com/knowledge/concepts/embedder/gemini/overview)
