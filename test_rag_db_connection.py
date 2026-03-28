#!/usr/bin/env python3
"""Teste de conexão RAG com Supabase (sem OpenAI)."""

import os
import sys

import psycopg
from dotenv import load_dotenv


load_dotenv()

def test_supabase_connection():
    """Testa conexão direta com Supabase."""

    db_url = os.getenv("SUPABASE_DB_URL")

    if not db_url:
        print("❌ SUPABASE_DB_URL não configurada")
        return False

    print("=" * 80)
    print("TESTE DE CONEXÃO SUPABASE RAG")
    print("=" * 80)
    print(f"Database URL: {db_url[:50]}...\n")

    try:
        # Testar conexão
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                # Verificar se tabela rag_chunks existe
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'juridico' AND table_name = 'chunks'
                    );
                """)
                row = cur.fetchone()
                table_exists = bool(row and row[0])

                if not table_exists:
                    print("❌ Tabela 'rag_chunks' não encontrada")
                    return False

                print("✅ Tabela 'rag_chunks' encontrada")

                # Contar chunks com embeddings
                cur.execute("""
                    SELECT COUNT(*)
                    FROM juridico.chunks
                    WHERE embedding IS NOT NULL;
                """)
                count_row = cur.fetchone()
                if count_row is None:
                    print("❌ Falha ao contar embeddings em rag_chunks")
                    return False
                count = count_row[0]

                print(f"✅ {count:,} chunks com embeddings")

                # Buscar um chunk de exemplo
                cur.execute("""
                    SELECT id, substring(texto, 1, 150) as texto_preview,
                           metadados->>'ano' as ano,
                           metadados->>'banca' as banca
                    FROM juridico.chunks
                    WHERE embedding IS NOT NULL
                    LIMIT 1;
                """)
                result = cur.fetchone()

                if result:
                    chunk_id, texto, ano, banca = result
                    print(f"\n📄 Chunk de exemplo:")
                    print(f"   ID: {chunk_id}")
                    print(f"   Ano: {ano}")
                    print(f"   Banca: {banca}")
                    print(f"   Texto: {texto}...")

                print("\n✅ Conexão com Supabase RAG funcionando!")
                return True

    except psycopg.Error as e:
        print(f"\n❌ Erro na conexão: {e}")
        return False

if __name__ == "__main__":
    success = test_supabase_connection()
    sys.exit(0 if success else 1)
