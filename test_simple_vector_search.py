"""Testa busca vetorial simples sem verificar dimensão."""

import os

import psycopg
from dotenv import load_dotenv


load_dotenv()

POSTGRES_URL = os.getenv("SUPABASE_DB_URL")

def main():
    print("🔍 Testando Vector Search (direto)...")

    if not POSTGRES_URL:
        raise RuntimeError("SUPABASE_DB_URL não configurada")

    try:
        with psycopg.connect(POSTGRES_URL) as conn:
            with conn.cursor() as cur:
                # Pegar um embedding de exemplo
                cur.execute("""
                    SELECT id, embedding
                    FROM rag_chunks
                    WHERE embedding IS NOT NULL
                    LIMIT 1;
                """)

                result = cur.fetchone()
                if result is None:
                    print("❌ Nenhum chunk com embedding encontrado")
                    return

                chunk_id, query_emb = result
                if not query_emb:
                    print(f"❌ Embedding vazio para chunk {chunk_id}")
                    return

                print(f"✅ Usando chunk {chunk_id} como query")

                # Busca vetorial simples
                cur.execute("""
                    SELECT
                        id,
                        documento_id,
                        substring(texto, 1, 200) as texto_preview,
                        metadados->>'ano' as ano,
                        metadados->>'banca' as banca,
                        1 - (embedding <=> %s::vector) as similarity
                    FROM rag_chunks
                    WHERE id != %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT 5;
                """, (query_emb, chunk_id, query_emb))

                results = cur.fetchall()

                print(f"\n✅ Encontrados {len(results)} chunks similares:\n")

                for i, (result_id, doc_id, texto, ano, banca, similarity) in enumerate(results, 1):
                    print(f"{i}. Similaridade: {similarity:.4f}")
                    print(f"   ID: {result_id}")
                    print(f"   Ano/Banca: {ano}/{banca}")
                    print(f"   Texto: {texto}")
                    print()
    except psycopg.Error as exc:
        print(f"❌ Erro ao consultar o banco: {exc}")

if __name__ == "__main__":
    main()
