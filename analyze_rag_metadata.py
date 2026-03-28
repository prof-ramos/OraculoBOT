"""Analisa metadados e estrutura dos chunks RAG."""

import os
import psycopg
import json
from dotenv import load_dotenv


load_dotenv()

POSTGRES_URL = os.getenv("SUPABASE_DB_URL")

def main():
    print("🔍 Analisando metadados RAG...")

    if not POSTGRES_URL:
        raise RuntimeError("SUPABASE_DB_URL não configurada")

    with psycopg.connect(POSTGRES_URL) as conn:
        with conn.cursor() as cur:
            # Amostra completa com metadados expandidos
            cur.execute("""
                SELECT
                    id,
                    document_id,
                    substring(content, 1, 200) as texto_preview,
                    metadata,
                    token_count,
                    created_at
                FROM juridico.chunks
                LIMIT 5;
            """)

            chunks = cur.fetchall()

            print(f"\n📊 Amostra de chunks com metadados:\n")

            for i, chunk in enumerate(chunks, 1):
                chunk_id, doc_id, texto, metadata, tokens, created = chunk

                print(f"{'='*80}")
                print(f"Chunk #{i}")
                print(f"{'='*80}")
                print(f"ID: {chunk_id}")
                print(f"Documento ID: {doc_id}")
                print(f"Tokens: {tokens}")
                print(f"Criado em: {created}")
                print(f"\nTexto (primeiros 200 chars):")
                print(f"  {texto}")
                print(f"\nMetadados completos:")
                if isinstance(metadata, dict):
                    print(json.dumps(metadata, indent=2, ensure_ascii=False))
                else:
                    print(f"  {metadata}")
                print()

            # Estatísticas dos metadados
            cur.execute("""
                SELECT
                    metadata->>'ano' as ano,
                    metadata->>'tipo' as tipo,
                    metadata->>'banca' as banca,
                    COUNT(*) as count
                FROM juridico.chunks
                GROUP BY ano, tipo, banca
                ORDER BY count DESC
                LIMIT 20;
            """)

            stats = cur.fetchall()

            print(f"\n📈 Distribuição por metadados (top 20):")
            print(f"{'Ano':<10} {'Tipo':<15} {'Banca':<20} {'Qtd':>10}")
            print("-" * 60)

            for ano, tipo, banca, count in stats:
                ano_str = ano or "N/A"
                tipo_str = tipo or "N/A"
                banca_str = banca or "N/A"
                print(f"{ano_str:<10} {tipo_str:<15} {banca_str:<20} {count:>10,}")

            # Exemplo de documento
            cur.execute("""
                SELECT
                    id,
                    nome,
                    chunk_count,
                    token_count,
                    substring(arquivo_origem, 1, 100) as arquivo
                FROM juridico.documents
                ORDER BY token_count DESC
                LIMIT 5;
            """)

            docs = cur.fetchall()

            print(f"\n📚 Maiores documentos (por tokens):\n")

            for doc_id, nome, chunks, tokens, arquivo in docs:
                chunks_display = f"{chunks:,}" if chunks is not None else "N/A"
                tokens_display = f"{tokens:,}" if tokens is not None else "N/A"
                print(f"ID: {doc_id}")
                print(f"Nome: {nome}")
                print(f"Chunks: {chunks_display}")
                print(f"Tokens: {tokens_display}")
                print(f"Arquivo: {arquivo}")
                print()

if __name__ == "__main__":
    main()
