"""RAG Retriever para busca semântica em legislação."""

import logging
from typing import Optional

import psycopg

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
    def conn(self):
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

        try:
            with self.conn.cursor() as cur:
                # Construir query base
                where_clauses = ["embedding IS NOT NULL"]
                params = []

                # Adicionar filtros se fornecidos
                if filters:
                    for key, value in filters.items():
                        if key not in ALLOWED_METADATA_FILTERS:
                            logger.warning("Ignorando filtro RAG não permitido: %s", key)
                            continue
                        where_clauses.append(f"metadados->>'{key}' = %s")
                        params.append(str(value))

                where_sql = " AND ".join(where_clauses)

                # Query de busca vetorial
                sql = f"""
                    SELECT
                        id,
                        documento_id,
                        texto,
                        metadados,
                        metadados->>'ano' as ano,
                        metadados->>'banca' as banca,
                        metadados->>'tipo' as tipo,
                        metadados->>'artigo' as artigo,
                        1 - (embedding <=> %s::vector) as similarity
                    FROM rag_chunks
                    WHERE {where_sql}
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s;
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

                params.extend([emb_str, emb_str, top_k])

                cur.execute(sql, params)
                results = cur.fetchall()

                # Montar resposta
                chunks = []
                for row in results:
                    chunk_id, doc_id, texto, metadata, ano, banca, tipo, artigo, similarity = row
                    chunks.append({
                        "id": chunk_id,
                        "documento_id": doc_id,
                        "texto": texto,
                        "metadados": metadata,
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
                        where_clauses.append(f"metadados->>'{key}' = %s")
                        params.append(str(value))

                where_sql = " AND ".join(where_clauses)

                sql = f"""
                    SELECT
                        id,
                        documento_id,
                        substring(texto, 1, 500) as texto_preview,
                        metadados,
                        metadados->>'ano' as ano,
                        metadados->>'banca' as banca
                    FROM rag_chunks
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
