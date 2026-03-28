"""RAG Retriever para busca semântica em legislação."""

from __future__ import annotations

import logging
from typing import Optional

import psycopg
from psycopg import sql as psql_sql

from oraculo_bot.config import SUPABASE_DB_URL

logger = logging.getLogger(__name__)
ALLOWED_METADATA_FILTERS = {
    "ano",
    "artigo",
    "assunto",
    "banca",
    "cargo",
    "disciplina",
    "tema",
    "tipo",
}


RAG_SCHEMA = "juridico"
CHUNKS_TABLE = f"{RAG_SCHEMA}.chunks"
DOCUMENTS_TABLE = f"{RAG_SCHEMA}.documents"
MATCH_FUNCTION = f"{RAG_SCHEMA}.match_chunks"


class RAGRetriever:
    """Retriever para RAG usando Supabase pgvector.

    Realiza busca semântica em chunks de legislação com embeddings.
    """

    def __init__(self, db_url: Optional[str] = None):
        """Inicializa o retriever.

        Args:
            db_url: URL PostgreSQL. Se None, usa SUPABASE_DB_URL.
        """
        self.db_url = db_url or SUPABASE_DB_URL
        self._conn = None

    @property
    def conn(self) -> psycopg.Connection:
        """Lazy connection."""
        if self._conn is None:
            if not self.db_url:
                raise RuntimeError("SUPABASE_DB_URL não configurada")
            self._conn = psycopg.connect(self.db_url)
        return self._conn

    @property
    def enabled(self) -> bool:
        """Verifica se RAG está habilitado."""
        return bool(self.db_url)

    def retrieve(
        self,
        query_text: str,
        query_embedding: list[float],
        top_k: int = 5,
        filters: Optional[dict] = None,
    ) -> list[dict]:
        """Busca chunks similares ao query.

        Args:
            query_text: Texto da query (não usado na busca vetorial).
            query_embedding: Embedding do query (vetor de floats).
            top_k: Número de resultados a retornar.
            filters: Filtros de metadados (ex: {"ano": "2021", "banca": "FCC"}).

        Returns:
            Lista de chunks similares com metadados.
        """
        if not self.enabled:
            logger.warning("RAG desabilitado (SUPABASE_DB_URL não configurada)")
            return []

        if query_embedding is None:
            logger.warning("Embedding None fornecido, retornando lista vazia")
            return []

        try:
            with self.conn.cursor() as cur:
                # Construir filtro de metadados seguro para a função SQL
                metadata_filter = {}
                if filters:
                    for key, value in filters.items():
                        if key not in ALLOWED_METADATA_FILTERS:
                            logger.warning("Ignorando filtro RAG não permitido: %s", key)
                            continue
                        metadata_filter[key] = value

                # Query de busca vetorial via função versionada no schema juridico
                sql = f"""
                    SELECT
                        id,
                        document_id,
                        content,
                        metadata,
                        metadata->>'ano' as ano,
                        metadata->>'banca' as banca,
                        metadata->>'tipo' as tipo,
                        metadata->>'artigo' as artigo,
                        similarity
                    FROM {MATCH_FUNCTION}(
                        %s::vector,
                        %s,
                        %s,
                        %s::jsonb,
                        %s
                    );
                """

                # Converter embedding para string PostgreSQL array
                # Garantir formato com colchetes [0.1, 0.2, ...]
                if isinstance(query_embedding, str):
                    # Se já for string, garantir colchetes
                    emb_str = query_embedding
                    if emb_str.startswith("("):
                        emb_str = "[" + emb_str[1:-1] + "]"
                else:
                    # Se for lista, converter para string com colchetes
                    emb_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

                metadata_filter_json = __import__("json").dumps(metadata_filter, ensure_ascii=False)
                params = [emb_str, top_k, 0.4, metadata_filter_json, None]

                cur.execute(sql, params)
                results = cur.fetchall()

                # Montar resposta
                chunks = []
                for row in results:
                    chunk_id, doc_id, texto, metadata, ano, banca, tipo, artigo, similarity = row
                    chunks.append({
                        "id": chunk_id,
                        "documento_id": doc_id,
                        "document_id": doc_id,
                        "texto": texto,
                        "content": texto,
                        "metadados": metadata,
                        "metadata": metadata,
                        "ano": ano,
                        "banca": banca,
                        "tipo": tipo,
                        "artigo": artigo,
                        "similarity": similarity,
                    })

                logger.info(f"RAG: encontrados {len(chunks)} chunks (top_k={top_k})")
                return chunks

        except psycopg.Error:
            logger.exception("Erro na busca RAG")
            return []

    def retrieve_by_keywords(
        self,
        keywords: list[str],
        top_k: int = 5,
        filters: Optional[dict] = None,
    ) -> list[dict]:
        """Busca chunks por keywords (full-text search).

        Args:
            keywords: Lista de palavras-chave.
            top_k: Número de resultados.
            filters: Filtros de metadados.

        Returns:
            Lista de chunks com keywords.
        """
        if not self.enabled:
            return []

        try:
            with self.conn.cursor() as cur:
                # Construir WHERE com ILIKE para cada keyword
                keyword_conditions = []
                params = []
                for keyword in keywords:
                    like_value = f"%{keyword}%"
                    keyword_conditions.append("(texto ILIKE %s OR metadados::text ILIKE %s)")
                    params.extend([like_value, like_value])

                where_clauses = ["embedding IS NOT NULL"]
                if keyword_conditions:
                    where_clauses.append("(" + " OR ".join(keyword_conditions) + ")")

                # Adicionar filtros se fornecidos
                if filters:
                    for key, value in filters.items():
                        if key not in ALLOWED_METADATA_FILTERS:
                            logger.warning("Ignorando filtro keyword não permitido: %s", key)
                            continue
                        where_clauses.append(f"metadata->>'{key}' = %s")
                        params.append(str(value))

                where_sql = " AND ".join(where_clauses)

                sql = f"""
                    SELECT
                        id,
                        document_id,
                        substring(content, 1, 500) as texto_preview,
                        metadata,
                        metadata->>'ano' as ano,
                        metadata->>'banca' as banca
                    FROM {CHUNKS_TABLE}
                    WHERE {where_sql}
                    LIMIT %s;
                """

                params.append(top_k)
                cur.execute(sql, params)
                results = cur.fetchall()

                chunks = []
                for row in results:
                    chunk_id, doc_id, texto, metadata, ano, banca = row
                    chunks.append({
                        "id": chunk_id,
                        "documento_id": doc_id,
                        "texto": texto,
                        "metadados": metadata,
                        "ano": ano,
                        "banca": banca,
                    })

                logger.info(f"RAG keyword search: {len(chunks)} chunks")
                return chunks

        except psycopg.Error:
            logger.exception("Erro na busca por keywords")
            return []
