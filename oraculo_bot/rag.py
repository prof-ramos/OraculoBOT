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


def create_retriever(db_url: Optional[str] = None) -> RAGRetriever:
    """Factory para RAGRetriever com injeção de dependência.

    Args:
        db_url: URL PostgreSQL. Se None, usa SUPABASE_DB_URL.

    Returns:
        Instância configurada de RAGRetriever.

    Example:
        retriever = create_retriever(db_url="postgres://test")
        context = retrieve_relevant_legislation("query", retriever=retriever)
    """
    return RAGRetriever(db_url=db_url)


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
        logger.info("RAG: sem API key OpenAI, usando fallback (busca por keywords)")


# Constante de stop words em português para extração de keywords
_PORTUGUESE_STOP_WORDS = {
    # Artigos e pronomes
    "o", "a", "os", "as", "um", "uma", "uns", "umas",
    "ele", "ela", "eles", "elas", "eu", "tu", "voce", "nos", "vos",
    "me", "te", "se", "lhe", "lhes", "nos", "vos",
    # Verbos comuns
    "e", "ser", "estar", "ter", "haver", "fazer", "dar", "dizer",
    "ir", "vir", "poder", "querer", "saber", "ver", "pensar",
    # Preposições e conjunções
    "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
    "por", "para", "como", "mas", "que", "qual", "quais",
    # Outros
    "muito", "pouco", "mais", "menos", "tambem", "ainda", "so",
    "nem", "ou", "ja", "onde", "quando", "como", "quem",
}


def extract_keywords(text: str, max_keywords: int = 10, min_length: int = 4) -> list[str]:
    """Extrai palavras-chave do texto para busca por keywords.

    Remove stop words em português, filtra palavras curtas e limita quantidade.

    Args:
        text: Texto da query do usuário.
        max_keywords: Número máximo de keywords a retornar.
        min_length: Tamanho mínimo das palavras (caracteres).

    Returns:
        Lista de keywords em minúsculas, sem duplicatas.
    """
    import re

    # Normalizar: lowercase
    text = text.lower()

    # Remove pontuação e mantém apenas letras/espacos
    text = re.sub(r"[^\w\s]", " ", text)

    # Tokenizar
    words = text.split()

    # Filtrar: remover stop words e palavras curtas
    keywords = [
        w for w in words
        if len(w) >= min_length and w not in _PORTUGUESE_STOP_WORDS
    ]

    # Remover duplicatas mantendo ordem
    seen = set()
    unique_keywords = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique_keywords.append(kw)

    # Limitar quantidade
    return unique_keywords[:max_keywords]


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
        chunks = []

        # Caminho 1: Busca semântica com embeddings (requer OpenAI)
        if _embedding_model:
            query_embedding = _embedding_model.get_embedding(query_text)
            logger.info(f"RAG: embedding gerado (dim={len(query_embedding)})")

            if not query_embedding:
                logger.error("RAG: impossível gerar embedding")
                return ""

            chunks = _rag_retriever.retrieve(
                query_text=query_text,
                query_embedding=query_embedding,
                top_k=top_k,
                filters=filters,
            )

        # Caminho 2: Fallback por keywords (sem OpenAI)
        else:
            keywords = extract_keywords(query_text)

            if keywords:
                logger.info(f"RAG: usando busca por keywords: {keywords}")
                chunks = _rag_retriever.retrieve_by_keywords(
                    keywords=keywords,
                    top_k=top_k,
                    filters=filters,
                )
            else:
                logger.warning("RAG: nenhuma keyword válida extraída da query")
                chunks = []

        if not chunks:
            return ""

        # Format chunks como contexto
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            # Keyword search não retorna 'similarity'
            similarity = chunk.get("similarity")
            texto = chunk.get("texto", "")
            ano = chunk.get("ano", "N/A")
            banca = chunk.get("banca", "N/A")
            tipo = chunk.get("tipo", "N/A")

            # Meta string condicional (sem similarity se keyword search)
            if similarity is not None:
                meta_str = f" (ano: {ano}, banca: {banca}, tipo: {tipo}, sim: {similarity:.2f})"
            else:
                meta_str = f" (ano: {ano}, banca: {banca}, tipo: {tipo})"

            context_parts.append(f"[Fonte {i}{meta_str}]")
            context_parts.append(texto)
            context_parts.append("")

        return "\n".join(context_parts)

    except Exception as e:
        logger.error(f"Erro na busca RAG: {e}")
        return ""
