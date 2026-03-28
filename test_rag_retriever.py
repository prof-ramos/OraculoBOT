#!/usr/bin/env python3
"""Teste do RAGRetriever (simulando fluxo sem OpenAI API)."""

import ast
import json
import os
import sys
import traceback

import psycopg
from dotenv import load_dotenv


load_dotenv()


def _parse_embedding(embedding: str | list[float]) -> list[float]:
    if not isinstance(embedding, str):
        return embedding
    try:
        values = json.loads(embedding)
    except json.JSONDecodeError:
        values = ast.literal_eval(embedding)
    return [float(value) for value in values]


def test_rag_retriever():
    """Testa RAGRetriever com embedding do banco."""

    from oraculo_bot.rag_retriever import RAGRetriever

    db_url = os.getenv("SUPABASE_DB_URL")

    if not db_url:
        print("❌ SUPABASE_DB_URL não configurada")
        return False

    print("=" * 80)
    print("TESTE DO RAGRETRIEVER")
    print("=" * 80)
    print()

    try:
        # 1. Criar retriever
        retriever = RAGRetriever()
        print(f"✅ RAGRetriever criado (enabled={retriever.enabled})")
        print()

        # 2. Pegar um embedding existente para teste
        print("2️⃣  Buscando embedding de referência...")
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, content, embedding
                    FROM juridico.chunks
                    WHERE embedding IS NOT NULL
                    ORDER BY random()
                    LIMIT 1;
                """)
                row = cur.fetchone()
                if row is None:
                    print("❌ Nenhum chunk com embedding encontrado")
                    return False
                chunk_id, texto, embedding = row

                # Converter para lista de floats
                emb_list = _parse_embedding(embedding)
                if not emb_list:
                    print(f"❌ Embedding vazio para chunk {chunk_id}")
                    return False

                print(f"✅ Embedding obtido: {chunk_id}")
                print(f"   Dimensão: {len(emb_list)}")
                print(f"   Texto: {texto[:100]}...")
                print()

        # 3. Usar RAGRetriever para buscar similares
        print("3️⃣  Buscando chunks similares via RAGRetriever...")
        results = retriever.retrieve(
            query_text="texto de teste",
            query_embedding=emb_list,
            top_k=3,
        )

        print(f"✅ Recuperados {len(results)} chunks")
        print()

        # 4. Mostrar resultados
        print("4️⃣  Resultados:")
        print("-" * 80)
        for i, chunk in enumerate(results, 1):
            similarity = chunk.get("similarity", 0)
            texto = chunk.get("texto", "")[:150]
            ano = chunk.get("ano", "N/A")
            banca = chunk.get("banca", "N/A")

            print(f"\n[{i}] Similaridade: {similarity:.2%}")
            print(f"    Ano: {ano} | Banca: {banca}")
            print(f"    Texto: {texto}...")

        print()
        print("-" * 80)
        print("\n✅ RAGRetriever funcionando perfeitamente!")
        return True

    except Exception as e:
        print(f"\n❌ Erro: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_rag_retriever()
    sys.exit(0 if success else 1)
