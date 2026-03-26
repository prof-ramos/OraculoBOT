"""Funções RAG para uso com Agno Agent."""

from __future__ import annotations

import logging
from typing import Optional

from agno.knowledge.embedder.openai import OpenAIEmbedder

from oraculo_bot.rag_retriever import RAGRetriever
from oraculo_bot.config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

# Instância global do retriever
_rag_retriever = RAGRetriever()

# Instância global de embeddings (para gerar embeddings de queries)
_embedding_model: Optional[OpenAIEmbedder] = None


def init_rag(api_key: Optional[str] = None) -> None:
    """Inicializa o RAG com modelo de embeddings OpenAI.

    Args:
        api_key: Chave API OpenAI para embeddings.
    """
    global _embedding_model

    if api_key:
        try:
            _embedding_model = OpenAIEmbedder(
                id="text-embedding-3-small",  # Modelo compatível com banco
                api_key=api_key
            )
            logger.info("RAG: modelo de embeddings OpenAI inicializado (1536 dims)")
        except Exception as e:
            logger.warning(f"RAG: erro ao inicializar embeddings OpenAI: {e}")
            _embedding_model = None
    else:
        logger.info("RAG: sem API key OpenAI, usando fallback (embeddings aleatórios)")


def retrieve_relevant_legislation(
    query_text: str,
    top_k: int = 5,
    filters: Optional[dict] = None,
) -> str:
    """Busca legislação relevante e retorna como contexto.

    Args:
        query_text: Texto da query do usuário.
        top_k: Número de chunks a recuperar.
        filters: Filtros de metadados (ex: {"ano": "2021", "banca": "FCC"}).

    Returns:
        String formatado com os chunks encontrados.
    """
    global _embedding_model

    # Auto-inicializar com OpenAI se disponível (prioridade sobre Gemini)
    if _embedding_model is None and OPENAI_API_KEY:
        init_rag(OPENAI_API_KEY)

    if not _rag_retriever.enabled:
        return ""

    try:
        # Gerar embedding da query se modelo disponível
        query_embedding = None
        if _embedding_model:
            query_embedding = _embedding_model.get_embedding(query_text)
            logger.info(f"RAG: embedding gerado (dim={len(query_embedding)})")
        else:
            # Fallback: pegar embedding de um chunk aleatório para teste
            import psycopg

            with psycopg.connect(_rag_retriever.db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT embedding
                        FROM rag_chunks
                        WHERE embedding IS NOT NULL
                        ORDER BY random()
                        LIMIT 1;
                    """)
                    result = cur.fetchone()
                    if result:
                        # Converter string para lista de floats
                        emb_str = result[0].strip("[]")
                        query_embedding = [float(x) for x in emb_str.split(",")]
                        logger.warning("RAG: usando embedding aleatório (fallback)")

        if not query_embedding:
            logger.error("RAG: impossível gerar embedding")
            return ""

        # Buscar chunks similares
        chunks = _rag_retriever.retrieve(
            query_text=query_text,
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters,
        )

        if not chunks:
            return ""

        # Format chunks como contexto
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            similarity = chunk.get("similarity", 0)
            texto = chunk.get("texto", "")
            ano = chunk.get("ano", "N/A")
            banca = chunk.get("banca", "N/A")
            tipo = chunk.get("tipo", "N/A")

            meta_str = f" (ano: {ano}, banca: {banca}, tipo: {tipo}, sim: {similarity:.2f})"

            context_parts.append(f"[Fonte {i}{meta_str}]")
            context_parts.append(texto)
            context_parts.append("")

        return "\n".join(context_parts)

    except Exception as e:
        logger.error(f"Erro na busca RAG: {e}")
        return ""
