"""Descobre todas as tabelas no Supabase PostgreSQL."""

import os
import psycopg

# Carrega variáveis de ambiente
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

POSTGRES_URL = os.getenv("SUPABASE_DB_URL")
if not POSTGRES_URL:
    raise ValueError(
        "SUPABASE_DB_URL não configurada. "
        "Configure a variável de ambiente ou crie um arquivo .env"
    )

def main():
    print("🔍 Conectando ao PostgreSQL...")

    with psycopg.connect(POSTGRES_URL) as conn:
        with conn.cursor() as cur:
            # Listar todas as tabelas
            cur.execute("""
                SELECT
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables
                WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
            """)

            tables = cur.fetchall()

            print(f"\n📊 Encontradas {len(tables)} tabelas:\n")

            for schema, table, size in tables:
                print(f"  • {schema}.{table} ({size})")

                # Contar registros
                cur.execute(f"SELECT COUNT(*) FROM {schema}.{table}")
                count = cur.fetchone()[0]
                print(f"    Registros: {count:,}")

                # Mostrar estrutura das tabelas promissoras
                if count > 0 and count < 1000:
                    cur.execute(f"""
                        SELECT column_name, data_type
                        FROM information_schema.columns
                        WHERE table_schema = '{schema}'
                        AND table_name = '{table}'
                        LIMIT 10;
                    """)
                    cols = cur.fetchall()
                    print(f"    Colunas: {', '.join([f'{c[0]}:{c[1]}' for c in cols])}")

                print()

            # Buscar tabelas com embeddings ou legislações
            print("\n🔍 Buscando tabelas com 'embedding' ou 'legisla' no nome...")
            cur.execute("""
                SELECT schemaname, tablename
                FROM pg_tables
                WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                AND (tablename ILIKE '%embedding%'
                     OR tablename ILIKE '%legisla%'
                     OR tablename ILIKE '%document%'
                     OR tablename ILIKE '%chunk%'
                     OR tablename ILIKE '%law%');
            """)

            relevant = cur.fetchall()

            if relevant:
                print(f"\n✅ Tabelas relevantes encontradas:\n")
                for schema, table in relevant:
                    print(f"  • {schema}.{table}")

                    # Mostrar amostra de dados
                    cur.execute(f"SELECT * FROM {schema}.{table} LIMIT 1")
                    sample = cur.fetchone()
                    if sample:
                        print(f"    Existe dados! Amostra não disponível (cursor)")
            else:
                print("\n❌ Nenhuma tabela relevante encontrada")

if __name__ == "__main__":
    main()
