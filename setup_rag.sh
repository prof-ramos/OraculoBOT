#!/bin/bash
# Script helper para configurar RAG no OraculoBOT

echo "=== Setup RAG - OraculoBOT ==="
echo ""
echo "Este script ajudará a configurar as variáveis de ambiente para o RAG."
echo ""

# Verificar se .env existe
if [ ! -f .env ]; then
    echo "⚠️  Arquivo .env não encontrado. Criando a partir do .env.example..."
    cp .env.example .env
    echo "✅ Arquivo .env criado."
fi

# Verificar variáveis já configuradas
source .env 2>/dev/null || true

echo ""
echo "Variáveis atuais:"
echo "  - DISCORD_BOT_TOKEN: ${DISCORD_BOT_TOKEN:+✅ Configurado}"
echo "  - DEEPSEEK_API_KEY: ${DEEPSEEK_API_KEY:+✅ Configurado}"
echo "  - OPENAI_API_KEY: ${OPENAI_API_KEY:+✅ Configurado}"
echo "  - SUPABASE_DB_URL: ${SUPABASE_DB_URL:+✅ Configurado}"
echo ""

# Se OPENAI_API_KEY não estiver configurada
if [ -z "$OPENAI_API_KEY" ]; then
    echo "📝 Para configurar o OPENAI_API_KEY:"
    echo "   1. Obtenha sua chave em https://platform.openai.com/api-keys"
    echo "   2. Adicione ao .env: OPENAI_API_KEY=sk-..."
    echo ""
fi

# Se SUPABASE_DB_URL não estiver configurada
if [ -z "$SUPABASE_DB_URL" ]; then
    echo "📝 Para configurar o SUPABASE_DB_URL:"
    echo "   Formato: postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres"
    echo "   Exemplo:"
    echo "   SUPABASE_DB_URL=\"postgresql://postgres:YOUR-PASSWORD@db.your-project.supabase.co:5432/postgres\""
    echo ""
fi

echo "=== Teste de Conexão ==="
echo ""
echo "Após configurar as variáveis, execute:"
echo "  uv run test_rag_integration.py"
echo ""
