#!/usr/bin/env python3
"""Teste rápido de configuração do Gemini Embeddings."""

import os
import sys

def test_gemini_setup():
    """Testa se Gemini API está configurada corretamente."""

    from dotenv import load_dotenv
    load_dotenv()

    print("=" * 80)
    print("TESTE DE CONFIGURAÇÃO - GEMINI EMBEDDINGS")
    print("=" * 80)
    print()

    # Verificar API key
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("❌ GEMINI_API_KEY não configurada")
        print()
        print("Para configurar:")
        print("1. Acesse: https://ai.google.dev/")
        print("2. Crie uma API key gratuita")
        print("3. Adicione ao .env: GEMINI_API_KEY=AIzaSy...")
        print()
        print("📖 Ver docs/GEMINI_SETUP.md para instruções detalhadas")
        return False

    print(f"✅ GEMINI_API_KEY configurada: {api_key[:10]}...")
    print()

    # Testar import
    try:
        from agno.knowledge.embedder.google import GeminiEmbedder
        print("✅ GeminiEmbedder importado com sucesso")
    except ImportError as e:
        print(f"❌ Erro ao importar GeminiEmbedder: {e}")
        print()
        print("Execute: uv sync")
        return False

    print()

    # Testar embedding
    try:
        print("2️⃣  Testando geração de embedding...")
        embedder = GeminiEmbedder(
            api_key=api_key,
            id="gemini-embedding-001",
            dimensions=1536  # Compatível com banco Supabase
        )

        text = "Qual é a competência da União para legislar sobre direito do trabalho?"
        embedding = embedder.get_embedding(text)

        print(f"✅ Embedding gerado com sucesso!")
        print(f"   - Dimensões: {len(embedding)}")
        print(f"   - Primeiros 5 valores: {embedding[:5]}")
        print(f"   - Texto: {text[:50]}...")
        print()

        return True

    except Exception as e:
        print(f"❌ Erro ao gerar embedding: {e}")
        print()
        print("Possíveis causas:")
        print("  - API key inválida")
        print("  - Sem conexão com internet")
        print("  - Limite de quota atingido")
        print()
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_gemini_setup()

    print("=" * 80)
    if success:
        print("✅ CONFIGURAÇÃO GEMINI FUNCIONANDO!")
        print()
        print("Próximos passos:")
        print("1. Teste RAG completo: uv run test_rag_simulated_message.py")
        print("2. Inicie o bot: uv run python -m oraculo_bot")
        print("3. Envie mensagem no Discord")
    else:
        print("⚠️  Configure GEMINI_API_KEY para usar RAG com embeddings gratuitos")
        print("   Ou use OPENAI_API_KEY como alternativa")
    print("=" * 80)

    sys.exit(0 if success else 1)
