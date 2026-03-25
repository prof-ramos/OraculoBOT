"""Verifica formato de armazenamento do embedding."""

import psycopg

POSTGRES_URL = "postgres://postgres.edckgpfzoditeiphilhy:Alcione2025**@aws-1-sa-east-1.pooler.supabase.com:5432/postgres?sslmode=require"

def main():
    print("🔍 Verificando formato do embedding...")

    with psycopg.connect(POSTGRES_URL) as conn:
        with conn.cursor() as cur:
            # Pegar um exemplo de embedding
            cur.execute("""
                SELECT
                    id,
                    embedding,
                    pg_typeof(embedding) as type
                FROM rag_chunks
                WHERE embedding IS NOT NULL
                LIMIT 1;
            """)

            result = cur.fetchone()

            if result:
                chunk_id, embedding, emb_type = result

                print(f"Chunk ID: {chunk_id}")
                print(f"Tipo PostgreSQL: {emb_type}")
                print(f"Tipo Python: {type(embedding)}")

                # Tentar converter
                print(f"\nConteúdo (primeiros 200 chars):")
                print(f"  {str(embedding)[:200]}")

                # Se for string, tentar parsear como array
                if isinstance(embedding, str):
                    print(f"\n✅ Embedding está armazenado como STRING")
                    print(f"   Precisa converter: embedding::vector[]")

                    # Tentar converter
                    try:
                        cur.execute("""
                            SELECT
                                id,
                                string_to_array(substring(embedding, 2, length(embedding)-2), ',')::float[] as vec_array,
                                array_length(string_to_array(substring(embedding, 2, length(embedding)-2), ','), 1) as dim
                            FROM rag_chunks
                            WHERE id = %s;
                        """, (chunk_id,))

                        result = cur.fetchone()
                        if result:
                            id, vec_array, dim = result
                            print(f"\n✅ Conversão funcionou!")
                            print(f"   Dimensão: {dim}")
                            print(f"   Array type: {type(vec_array)}")
                            print(f"   Primeiros valores: {vec_array[:5] if vec_array else 'N/A'}")
                    except Exception as e:
                        print(f"\n❌ Erro na conversão: {e}")

if __name__ == "__main__":
    main()
