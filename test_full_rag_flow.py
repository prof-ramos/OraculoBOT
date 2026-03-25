#!/usr/bin/env python3
"""Teste completo do fluxo RAG do OraculoBOT."""

import os
import psycopg

def test_full_rag_flow():
    """Testa o fluxo completo de enriquecimento RAG."""

    from dotenv import load_dotenv
    load_dotenv()

    from oraculo_bot.rag_retriever import RAGRetriever

    db_url = os.getenv("SUPABASE_DB_URL")

    if not db_url:
        print("❌ SUPABASE_DB_URL não configurada")
        return False

    print("=" * 80)
    print("TESTE COMPLETO DO FLUXO RAG")
    print("=" * 80)
    print()

    # Query típica de usuário Discord
    query = "Qual é a competência da União para legislar sobre direito do trabalho?"
    print(f"📝 Query do usuário: {query}")
    print()

    try:
        # 1. Obter embedding de referência (simulando OpenAI API)
        print("1️⃣  Obtendo embedding (simulado)...")
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT embedding
                    FROM rag_chunks
                    WHERE embedding IS NOT NULL
                    AND texto ILIKE '%competência%'
                    AND texto ILIKE '%união%'
                    ORDER BY random()
                    LIMIT 1;
                """)
                result = cur.fetchone()

                if not result:
                    # Fallback: pegar qualquer embedding
                    cur.execute("""
                        SELECT embedding
                        FROM rag_chunks
                        WHERE embedding IS NOT NULL
                        ORDER BY random()
                        LIMIT 1;
                    """)
                    result = cur.fetchone()

                if result:
                    emb_string = result[0]
                    # Converter string para lista de floats
                    if isinstance(emb_string, str):
                        if emb_string.startswith("["):
                            import json
                            query_embedding = json.loads(emb_string.replace("'", '"'))
                        else:
                            # Formato (x, y, z)
                            query_embedding = [float(x) for x in emb_string.strip("()").split(",")]
                    else:
                        query_embedding = list(emb_string)

                    print(f"✅ Embedding obtido: {len(query_embedding)} dimensões")
                else:
                    print("❌ Nenhum embedding encontrado")
                    return False

        # 2. Buscar chunks similares via RAGRetriever
        print()
        print("2️⃣  Buscando legislação relevante...")
        retriever = RAGRetriever()
        chunks = retriever.retrieve(
            query_text=query,
            query_embedding=query_embedding,
            top_k=3
        )

        if not chunks:
            print("⚠️  Nenhum chunk encontrado")
            return False

        print(f"✅ Encontrados {len(chunks)} chunks relevantes")
        print()

        # 3. Formatar contexto RAG (como o bot.py faz)
        print("3️⃣  Contexto RAG gerado:")
        print("-" * 80)

        rag_context_parts = []
        for i, chunk in enumerate(chunks, 1):
            similarity = chunk.get("similarity", 0)
            texto = chunk.get("texto", "")
            ano = chunk.get("ano", "N/A")
            banca = chunk.get("banca", "N/A")
            tipo = chunk.get("tipo", "N/A")

            meta_str = f" (ano: {ano}, banca: {banca}, tipo: {tipo}, sim: {similarity:.2f})"
            chunk_str = f"[Fonte {i}{meta_str}]\n{texto}\n"

            rag_context_parts.append(chunk_str)
            print(chunk_str)

        print("-" * 80)
        print()

        # 4. Simular contexto completo do Discord
        print("4️⃣  Contexto completo do Discord message:")
        print("-" * 80)

        discord_context = f"""
Discord username: UsuarioTeste
Discord userid: 123456789
Discord url: https://discord.com/channels/123/456/789
Session mode: estudo
Previous messages count: 0

[CONTEXTO LEGISLATIVO RELEVANTE]
{"".join(rag_context_parts)}
"""
        print(discord_context)
        print("-" * 80)
        print()

        print("✅ Fluxo RAG completo funcionando!")
        print()
        print("📊 Resumo:")
        print(f"   - Query: {query[:60]}...")
        print(f"   - Chunks recuperados: {len(chunks)}")
        print(f"   - Similaridade média: {sum(c['similarity'] for c in chunks) / len(chunks):.2%}")
        print()
        return True

    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_full_rag_flow()
    exit(0 if success else 1)
