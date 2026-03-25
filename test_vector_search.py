"""Testa busca vetorial similarity no Supabase."""

import psycopg
import json

POSTGRES_URL = "postgres://postgres.edckgpfzoditeiphilhy:Alcione2025**@aws-1-sa-east-1.pooler.supabase.com:5432/postgres?sslmode=require"

def main():
    print("🔍 Testando Vector Search...")

    with psycopg.connect(POSTGRES_URL) as conn:
        with conn.cursor() as cur:
            # Primeiro, pegar dimensão do embedding
            cur.execute("""
                SELECT
                    dim(embedding) as dim,
                    embedding
                FROM rag_chunks
                LIMIT 1;
            """)

            result = cur.fetchone()

            if result:
                dim, example_emb = result
                print(f"✅ Dimensão do embedding: {dim}")

                # Query de exemplo: buscar top 5 chunks similares
                # Vou usar um vetor de exemplo para teste
                query_embedding = example_emb

                print(f"\n🔎 Buscando chunks similares...")

                cur.execute("""
                    SELECT
                        id,
                        documento_id,
                        substring(texto, 1, 150) as texto_preview,
                        metadados->>'ano' as ano,
                        metadados->>'banca' as banca,
                        metadados->>'artigo' as artigo,
                        1 - (embedding <=> %s::vector) as similarity
                    FROM rag_chunks
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> %s::vector
                    LIMIT 5;
                """, (json.dumps(query_embedding), json.dumps(query_embedding)))

                results = cur.fetchall()

                print(f"\n✅ Encontrados {len(results)} chunks similares:\n")

                for i, (chunk_id, doc_id, texto, ano, banca, artigo, similarity) in enumerate(results, 1):
                    print(f"{i}. Similaridade: {similarity:.4f}")
                    print(f"   ID: {chunk_id}")
                    print(f"   Doc: {doc_id}")
                    print(f"   Ano/Banca: {ano}/{banca}")
                    print(f"   Artigo: {artigo}")
                    print(f"   Texto: {texto}")
                    print()

                # Exemplo com filtro de metadados
                print("🔍 Busca com filtros (apenas banca='FCC'):")

                cur.execute("""
                    SELECT
                        COUNT(*) as count
                    FROM rag_chunks
                    WHERE metadados->>'banca' = 'FCC'
                    AND embedding IS NOT NULL;
                """)

                fcc_count = cur.fetchone()[0]
                print(f"✅ Chunks da banca FCC: {fcc_count}")

                if fcc_count > 0:
                    cur.execute("""
                        SELECT
                            id,
                            substring(texto, 1, 150) as texto_preview,
                            metadados->>'ano' as ano,
                            1 - (embedding <=> %s::vector) as similarity
                        FROM rag_chunks
                        WHERE metadados->>'banca' = 'FCC'
                        AND embedding IS NOT NULL
                        ORDER BY embedding <=> %s::vector
                        LIMIT 3;
                    """, (json.dumps(query_embedding), json.dumps(query_embedding)))

                    fcc_results = cur.fetchall()

                    print(f"\n✅ Top 3 FCC similares:\n")
                    for i, (chunk_id, texto, ano, similarity) in enumerate(fcc_results, 1):
                        print(f"{i}. Similaridade: {similarity:.4f}")
                        print(f"   ID: {chunk_id}")
                        print(f"   Ano: {ano}")
                        print(f"   Texto: {texto}")
                        print()

if __name__ == "__main__":
    main()
