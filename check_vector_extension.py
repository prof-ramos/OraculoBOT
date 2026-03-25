"""Verifica se pgvector está instalado e configuração vetorial."""

import os

import psycopg
from dotenv import load_dotenv


load_dotenv()

POSTGRES_URL = os.getenv("SUPABASE_DB_URL")

def main():
    print("🔍 Verificando pgvector e configuração vetorial...")

    if not POSTGRES_URL:
        raise RuntimeError("SUPABASE_DB_URL não configurada")

    with psycopg.connect(POSTGRES_URL) as conn:
        with conn.cursor() as cur:
            # Verificar pgvector
            try:
                cur.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector';")
                result = cur.fetchone()
                if result:
                    print(f"✅ pgvector instalado: versão {result[0]}")
                else:
                    print("⚠️  pgvector não encontrado - instalando...")
                    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                    conn.commit()
                    print("✅ pgvector instalado!")
            except psycopg.Error as e:
                print(f"❌ Erro ao verificar pgvector: {e}")
                raise SystemExit(1) from e

            # Verificar tipo da coluna embedding
            cur.execute("""
                SELECT
                    column_name,
                    data_type,
                    udt_name
                FROM information_schema.columns
                WHERE table_name = 'rag_chunks'
                AND column_name = 'embedding';
            """)

            result = cur.fetchone()

            if result:
                col_name, data_type, udt_name = result
                print(f"\n📊 Coluna embedding:")
                print(f"  Nome: {col_name}")
                print(f"  Tipo SQL: {data_type}")
                print(f"  Tipo UDT: {udt_name}")

                # Verificar se há índice vetorial
                cur.execute("""
                    SELECT
                        indexname,
                        indexdef
                    FROM pg_indexes
                    WHERE tablename = 'rag_chunks'
                    AND indexname LIKE '%embedding%';
                """)

                indexes = cur.fetchall()

                if indexes:
                    print(f"\n📌 Índices vetoriais encontrados:")
                    for idx_name, idx_def in indexes:
                        print(f"  • {idx_name}")
                        print(f"    {idx_def}")
                else:
                    print("\n⚠️  Nenhum índice vetorial encontrado")
                    print("   Recomendação: Criar índice HNSW para similarity search")

                # Contar embeddings não nulos
                cur.execute("""
                    SELECT
                        COUNT(*) as total,
                        COUNT(embedding) as with_embedding,
                        COUNT(*) - COUNT(embedding) as null_embedding
                    FROM rag_chunks;
                """)

                stats = cur.fetchone()

                if stats:
                    total, with_emb, null_emb = stats
                    print(f"\n📈 Estatísticas de embeddings:")
                    print(f"  Total de chunks: {total:,}")
                    print(f"  Com embedding: {with_emb:,}")
                    print(f"  Sem embedding: {null_emb:,}")

                    # Pegar dimensão de um exemplo
                    if with_emb > 0:
                        cur.execute("""
                            SELECT embedding
                            FROM rag_chunks
                            WHERE embedding IS NOT NULL
                            LIMIT 1;
                        """)
                        result = cur.fetchone()

                        if result and result[0]:
                            emb = result[0]
                            if isinstance(emb, list):
                                dim = len(emb)
                                print(f"  Dimensão: {dim}")
                                print("  Exemplo: valores omitidos para evitar expor embeddings")
                            else:
                                print(f"  Tipo: {type(emb)}")

if __name__ == "__main__":
    main()
