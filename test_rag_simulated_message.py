#!/usr/bin/env python3
"""Teste simulado de mensagem Discord com RAG."""

import os
import sys

def test_simulated_message():
    """Simula o processamento de uma mensagem Discord com RAG."""

    print("=" * 80)
    print("TESTE SIMULADO - MENSAGEM DISCORD COM RAG")
    print("=" * 80)
    print()

    # Simular mensagem do usuário
    message_content = "Qual é a competência da União para legislar sobre direito do trabalho?"

    print(f"📝 Mensagem do usuário: {message_content}")
    print()

    # Importar funções do bot
    from oraculo_bot.agent import enrich_with_rag
    from textwrap import dedent

    # Contexto Discord simulado
    user_name = "UsuarioTeste"
    user_id = 123456789
    mode = "estudo"
    history_count = 0

    context = dedent(f"""
        Discord username: {user_name}
        Discord userid: {user_id}
        Discord url: https://discord.com/channels/1283924742851661844/1486301006659715143/123
        Session mode: {mode}
        Previous messages count: {history_count}
    """)

    print("1️⃣  Contexto Discord:")
    print("-" * 80)
    print(context)
    print("-" * 80)
    print()

    # Enriquecer com RAG
    print("2️⃣  Enriquecendo com RAG...")
    rag_context = enrich_with_rag(message_content, top_k=3)

    if rag_context:
        print("✅ Contexto RAG recuperado:")
        print("-" * 80)
        print(rag_context[:1000] + "..." if len(rag_context) > 1000 else rag_context)
        print("-" * 80)
        print()
    else:
        print("⚠️  Nenhum contexto RAG recuperado (usando fallback)")
        print()

    # Combinar contextos
    full_context = context + rag_context

    print("3️⃣  Contexto completo enviado ao Agno Agent:")
    print("=" * 80)
    print(full_context[:2000] + "..." if len(full_context) > 2000 else full_context)
    print("=" * 80)
    print()

    # Estatísticas
    rag_lines = rag_context.count('\n') if rag_context else 0
    rag_chars = len(rag_context) if rag_context else 0

    print("📊 Estatísticas:")
    print(f"   - Contexto Discord: {len(context)} caracteres")
    print(f"   - Contexto RAG: {rag_chars} caracteres, ~{rag_lines} linhas")
    print(f"   - Total: {len(full_context)} caracteres")
    print()

    # Verificar se RAG está funcionando
    if "CONTEXTO LEGISLATIVO RELEVANTE" in rag_context:
        print("✅ RAG funcionando perfeitamente!")
        print("   O bot recuperou legislação relevante para enriquecer a resposta.")
        return True
    elif rag_context:
        print("⚠️  RAG recuperou contexto, mas formato pode não ser o esperado.")
        print("   Conteúdo recuperado, verifique se está correto.")
        return True
    else:
        print("⚠️  RAG não recuperou contexto.")
        print("   Possíveis causas:")
        print("   - OPENAI_API_KEY não configurada")
        print("   - Supabase connection falhou")
        print("   - Nenhum chunk encontrado")
        return False

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    try:
        success = test_simulated_message()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
