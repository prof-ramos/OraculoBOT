#!/usr/bin/env python3
"""Teste de busca vetorial RAG (sem OpenAI API)."""

import os
import psycopg

def test_vector_search():
    """Testa busca vetorial usando um embedding existente do banco."""

    from dotenv import load_dotenv
    load_dotenv()

    db_url = os.getenv("SUPABASE_DB_URL")

    if not db_url:
        print("❌ SUPABASE_DB_URL não configurada")
        return False

    print("=" * 80)
    print("TESTE DE BUSCA VETORIAL RAG")
    print("=" * 80)
    print()

    try:
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                # 1. Pegar um chunk aleatório com embedding
                print("1️⃣  Buscando chunk de referência...")
                cur.execute("""
                    SELECT id, texto, embedding, metadata->>'ano' as ano, metadata->>'banca' as banca
                    FROM juridico.chunks
                    WHERE embedding IS NOT NULL
                    ORDER BY random()
                    LIMIT 1;
                """)
                ref_chunk = cur.fetchone()

                if not ref_chunk:
                    print("❌ Nenhum chunk com embedding encontrado")
                    return False

                chunk_id, texto, embedding, ano, banca = ref_chunk
                print(f"✅ Chunk de referência: {chunk_id}")
                print(f"   Ano: {ano} | Banca: {banca}")
                print(f"   Texto: {texto[:150]}...")
                print()

                # 2. Buscar chunks similares usando o embedding
                print("2️⃣  Buscando chunks similares...")
                emb_str = str(embedding)

                cur.execute("""
                    SELECT
                        id,
                        substring(content, 1, 200) as texto_preview,
                        metadata->>'ano' as ano,
                        metadata->>'banca' as banca,
                        1 - (embedding <=> %s::vector) as similarity
                    FROM juridico.chunks
                    WHERE id != %s AND embedding IS NOT NULL
                    ORDER BY embedding <=> %s::vector
                    LIMIT 5;
                """, (emb_str, chunk_id, emb_str))

                results = cur.fetchall()
                print(f"✅ Encontrados {len(results)} chunks similares")
                print()

                # 3. Mostrar resultados
                print("3️⃣  Resultados:")
                print("-" * 80)
                for i, (rid, rtexto, rano, rbanca, rsim) in enumerate(results, 1):
                    print(f"\n[{i}] Similaridade: {rsim:.2%}")
                    print(f"    ID: {rid}")
                    print(f"    Ano: {rano} | Banca: {rbanca}")
                    print(f"    Texto: {rtexto}...")

                print()
                print("-" * 80)
                print("\n✅ Busca vetorial funcionando perfeitamente!")
                return True

    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_vector_search()
    exit(0 if success else 1)
