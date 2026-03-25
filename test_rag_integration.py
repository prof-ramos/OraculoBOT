#!/usr/bin/env python3
"""Teste da integração RAG completa."""

from oraculo_bot.agent import enrich_with_rag

def test_rag_enrichment():
    """Testa se o RAG consegue enriquecer uma query com legislação relevante."""

    # Query sobre direito constitucional
    query = "Qual é a competência da União para legislar sobre direito do trabalho?"

    print("=" * 80)
    print("TESTE DE INTEGRAÇÃO RAG")
    print("=" * 80)
    print(f"\nQuery: {query}\n")

    # Chama a função de enriquecimento
    rag_context = enrich_with_rag(query, top_k=3)

    if rag_context:
        print("✅ RAG context recuperado com sucesso!\n")
        print("-" * 80)
        print("CONTEÚDO RAG:")
        print("-" * 80)
        print(rag_context)
        print("-" * 80)
        print("\n✅ Integração RAG funcionando corretamente!")
        return True
    else:
        print("⚠️  Nenhum contexto RAG recuperado.")
        print("Possíveis causas:")
        print("  - OPENAI_API_KEY não configurada")
        print("  - Supabase connection falhou")
        print("  - Nenhum chunk similar encontrado")
        return False

if __name__ == "__main__":
    success = test_rag_enrichment()
    exit(0 if success else 1)
