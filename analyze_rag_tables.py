"""Analisa estrutura detalhada das tabelas RAG do Supabase."""

import os

import psycopg
from psycopg import sql
from dotenv import load_dotenv

load_dotenv()

POSTGRES_URL = os.getenv("SUPABASE_DB_URL")

def analyze_table(conn, table_name):
    """Analisa estrutura e conteúdo de uma tabela."""
    print(f"\n{'='*80}")
    print(f"📊 TABELA: {table_name}")
    print('='*80)

    with conn.cursor() as cur:
        # Estrutura da tabela
        cur.execute("""
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = %s
            AND table_schema = %s
            ORDER BY ordinal_position;
        """, (table_name, "public"))

        columns = cur.fetchall()

        print("\n🔧 Estrutura:")
        for col in columns:
            nullable = "NULL" if col[2] == "YES" else "NOT NULL"
            default = f" DEFAULT {col[3]}" if col[3] else ""
            print(f"  • {col[0]}: {col[1]} {nullable}{default}")

        # Amostra de dados
        cur.execute(sql.SQL("SELECT * FROM {} LIMIT 2").format(sql.Identifier(table_name)))
        samples = cur.fetchall()

        if samples:
            # Pegar nomes das colunas
            col_names = [desc[0] for desc in cur.description]
            print(f"\n📄 Amostra ({len(samples)} registros):")

            for i, row in enumerate(samples, 1):
                print(f"\n  Registro #{i}:")
                for idx, (col, val) in enumerate(zip(col_names, row)):
                    # Truncar valores longos
                    val_str = str(val)
                    if len(val_str) > 100:
                        val_str = val_str[:100] + "..."
                    print(f"    {col}: {val_str}")

        # Estatísticas
        cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table_name)))
        count_row = cur.fetchone()
        count = count_row[0] if count_row else 0
        print(f"\n📦 Total de registros: {count:,}")

def main():
    print("🔍 Analisando tabelas RAG do Supabase...")

    if not POSTGRES_URL:
        raise RuntimeError("SUPABASE_DB_URL não configurada")

    with psycopg.connect(POSTGRES_URL) as conn:
        # Analizar rag_chunks primeiro (maior tabela)
        analyze_table(conn, "rag_chunks")

        # Analizar rag_documents
        analyze_table(conn, "rag_documents")

        # Analizar topics
        analyze_table(conn, "topics")

        print(f"\n{'='*80}")
        print("✅ Análise concluída!")
        print('='*80)

if __name__ == "__main__":
    main()
