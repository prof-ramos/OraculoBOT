"""Camada de persistencia para o pipeline de ingestao RAG Lote 1.

Implementa o repositorio conforme especificado em:
- docs/RAG_LOTE1/PASSO_5_ESPECIFICACAO_IMPLEMENTACAO.md
- docs/RAG_LOTE1/IMPLEMENTATION_TODO.md (EPIC 1, Tarefa 1.3)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

import psycopg
from psycopg import sql

from oraculo_bot.ingestion.models import (
    DocumentChunk,
    DocumentQuarantine,
    IngestionRun,
    RetrievalEvalRun,
    SourceDocument,
    StatusDocumento,
    StatusIngestaoRun,
    StatusReview,
)

SCHEMA_JURIDICO = "juridico"


class IngestionRepository:
    """Repositorio para operacoes de persistencia do pipeline de ingestao.

    Centraliza todas as operacoes de banco de dados relacionadas ao pipeline RAG.
    Usa psycopg direto para compatibilidade com o resto do projeto.
    """

    def __init__(self, db_url: Optional[str] = None) -> None:
        """Inicializa o repositorio.

        Args:
            db_url: URL de conexao PostgreSQL. Se None, usa SUPABASE_DB_URL.
                Se string vazia, desabilita explicitamente a persistencia.
        """
        if db_url is None:
            try:
                from oraculo_bot.config import SUPABASE_DB_URL
            except Exception:
                SUPABASE_DB_URL = ""
            self.db_url = SUPABASE_DB_URL
        else:
            self.db_url = db_url
        self._conn: Optional[psycopg.Connection] = None

    @property
    def conn(self) -> psycopg.Connection:
        """Conexao lazy."""
        if self._conn is None:
            if not self.db_url:
                raise RuntimeError("SUPABASE_DB_URL nao configurada")
            self._conn = psycopg.connect(self.db_url)
        return self._conn

    @property
    def enabled(self) -> bool:
        """Verifica se a persistencia esta habilitada."""
        return bool(self.db_url)

    def close(self) -> None:
        """Fecha a conexao com o banco."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _commit_or_rollback(self, action) -> Any:
        """Executa escrita com rollback em caso de erro."""
        try:
            result = action()
            self.conn.commit()
            return result
        except Exception:
            self.conn.rollback()
            raise

    # ─────────────────────────────────────────────────────────────────────────
    # INGESTION RUNS
    # ─────────────────────────────────────────────────────────────────────────

    def create_ingestion_run(
        self,
        run_key: str,
        lote: str,
        bloco_logico: str,
        pasta_origem: str,
        created_by: str = "system",
        observacoes: Optional[str] = None,
    ) -> IngestionRun:
        """Cria uma nova rodada de ingestao."""
        started_at = datetime.now(timezone.utc)

        if not self.enabled:
            return IngestionRun(
                run_key=run_key,
                lote=lote,
                bloco_logico=bloco_logico,
                pasta_origem=pasta_origem,
                status=StatusIngestaoRun.RUNNING,
                started_at=started_at,
                created_by=created_by,
                observacoes=observacoes,
            )

        def _action() -> IngestionRun:
            with self.conn.cursor() as cur:
                cur.execute(
                    sql.SQL(
                        """
                        INSERT INTO {}.ingestion_runs
                        (run_key, lote, bloco_logico, pasta_origem, status, started_at, created_by, observacoes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id, created_at
                        """
                    ).format(sql.Identifier(SCHEMA_JURIDICO)),
                    [
                        run_key,
                        lote,
                        bloco_logico,
                        pasta_origem,
                        StatusIngestaoRun.RUNNING.value,
                        started_at,
                        created_by,
                        observacoes,
                    ],
                )
                row = cur.fetchone()

            return IngestionRun(
                id=row[0],
                run_key=run_key,
                lote=lote,
                bloco_logico=bloco_logico,
                pasta_origem=pasta_origem,
                status=StatusIngestaoRun.RUNNING,
                started_at=started_at,
                created_by=created_by,
                observacoes=observacoes,
                created_at=row[1],
            )

        return self._commit_or_rollback(_action)

    def finalize_ingestion_run(
        self,
        run_id: UUID,
        status: StatusIngestaoRun,
        stats_json: Optional[Dict[str, Any]] = None,
    ) -> Optional[IngestionRun]:
        """Finaliza uma rodada de ingestao."""
        if not self.enabled:
            return None

        finished_at = datetime.now(timezone.utc)

        def _action() -> Optional[IngestionRun]:
            with self.conn.cursor() as cur:
                cur.execute(
                    sql.SQL(
                        """
                        UPDATE {}.ingestion_runs
                        SET status = %s, finished_at = %s, stats_json = %s
                        WHERE id = %s
                        RETURNING run_key, lote, bloco_logico, pasta_origem, started_at,
                                  created_by, observacoes, created_at
                        """
                    ).format(sql.Identifier(SCHEMA_JURIDICO)),
                    [
                        status.value,
                        finished_at,
                        json.dumps(stats_json) if stats_json else None,
                        run_id,
                    ],
                )
                row = cur.fetchone()

            if not row:
                return None

            return IngestionRun(
                id=run_id,
                run_key=row[0],
                lote=row[1],
                bloco_logico=row[2],
                pasta_origem=row[3],
                status=status,
                started_at=row[4],
                finished_at=finished_at,
                created_by=row[5],
                observacoes=row[6],
                stats_json=stats_json,
                created_at=row[7],
            )

        return self._commit_or_rollback(_action)

    def get_ingestion_run_by_key(self, run_key: str) -> Optional[IngestionRun]:
        """Busca uma rodada de ingestao pela chave."""
        if not self.enabled:
            return None

        with self.conn.cursor() as cur:
            cur.execute(
                sql.SQL(
                    """
                    SELECT id, run_key, lote, bloco_logico, pasta_origem, status,
                           started_at, finished_at, created_by, observacoes,
                           stats_json, created_at
                    FROM {}.ingestion_runs
                    WHERE run_key = %s
                    """
                ).format(sql.Identifier(SCHEMA_JURIDICO)),
                [run_key],
            )
            row = cur.fetchone()

        if row:
            return IngestionRun(
                id=row[0],
                run_key=row[1],
                lote=row[2],
                bloco_logico=row[3],
                pasta_origem=row[4],
                status=StatusIngestaoRun(row[5]),
                started_at=row[6],
                finished_at=row[7],
                created_by=row[8],
                observacoes=row[9],
                stats_json=row[10],
                created_at=row[11],
            )
        return None

    # ─────────────────────────────────────────────────────────────────────────
    # SOURCE DOCUMENTS
    # ─────────────────────────────────────────────────────────────────────────

    def register_source_document(
        self,
        ingestion_run_id: UUID,
        documento_id_externo: str,
        arquivo_origem: str,
        arquivo_nome: str,
        pasta_origem: str,
        bloco_logico: str,
        hash_sha256: str,
        extensao: str,
        tamanho_bytes: int,
        ramo: Optional[str] = None,
        fonte_tipo: Optional[str] = None,
        autoridade: Optional[str] = None,
        peso_confianca: Optional[str] = None,
    ) -> SourceDocument:
        """Registra um novo documento fonte."""
        if not self.enabled:
            return SourceDocument(
                ingestion_run_id=ingestion_run_id,
                documento_id_externo=documento_id_externo,
                arquivo_origem=arquivo_origem,
                arquivo_nome=arquivo_nome,
                pasta_origem=pasta_origem,
                bloco_logico=bloco_logico,
                hash_sha256=hash_sha256,
                extensao=extensao,
                tamanho_bytes=tamanho_bytes,
                ramo=ramo or SourceDocument.ramo,
                fonte_tipo=fonte_tipo or SourceDocument.fonte_tipo,
                autoridade=autoridade or SourceDocument.autoridade,
                peso_confianca=peso_confianca or SourceDocument.peso_confianca,
            )

        def _action() -> SourceDocument:
            with self.conn.cursor() as cur:
                cur.execute(
                    sql.SQL(
                        """
                        INSERT INTO {}.source_documents
                        (ingestion_run_id, documento_id_externo, arquivo_origem, arquivo_nome,
                         pasta_origem, bloco_logico, hash_sha256, extensao, tamanho_bytes,
                         ramo, fonte_tipo, autoridade, peso_confianca)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id, created_at
                        """
                    ).format(sql.Identifier(SCHEMA_JURIDICO)),
                    [
                        ingestion_run_id,
                        documento_id_externo,
                        arquivo_origem,
                        arquivo_nome,
                        pasta_origem,
                        bloco_logico,
                        hash_sha256,
                        extensao,
                        tamanho_bytes,
                        ramo,
                        fonte_tipo,
                        autoridade,
                        peso_confianca,
                    ],
                )
                row = cur.fetchone()

            return SourceDocument(
                id=row[0],
                ingestion_run_id=ingestion_run_id,
                documento_id_externo=documento_id_externo,
                arquivo_origem=arquivo_origem,
                arquivo_nome=arquivo_nome,
                pasta_origem=pasta_origem,
                bloco_logico=bloco_logico,
                hash_sha256=hash_sha256,
                extensao=extensao,
                tamanho_bytes=tamanho_bytes,
                ramo=ramo or SourceDocument.ramo,
                fonte_tipo=fonte_tipo or SourceDocument.fonte_tipo,
                autoridade=autoridade or SourceDocument.autoridade,
                peso_confianca=peso_confianca or SourceDocument.peso_confianca,
                created_at=row[1],
            )

        return self._commit_or_rollback(_action)

    def update_document_extraction(
        self,
        document_id: UUID,
        texto_extraido: Optional[str],
        extracao_status: str,
        extracao_metodo: Optional[str] = None,
    ) -> Optional[SourceDocument]:
        """Atualiza dados de extracao de um documento."""
        if not self.enabled:
            return None

        updated_at = datetime.now(timezone.utc)

        def _action() -> Optional[SourceDocument]:
            with self.conn.cursor() as cur:
                cur.execute(
                    sql.SQL(
                        """
                        UPDATE {}.source_documents
                        SET texto_extraido = %s, extracao_status = %s,
                            extracao_metodo = %s, updated_at = %s
                        WHERE id = %s
                        RETURNING ingestion_run_id, documento_id_externo, arquivo_origem,
                                  arquivo_nome, pasta_origem, bloco_logico, hash_sha256,
                                  extensao, tamanho_bytes, created_at
                        """
                    ).format(sql.Identifier(SCHEMA_JURIDICO)),
                    [
                        texto_extraido,
                        extracao_status,
                        extracao_metodo,
                        updated_at,
                        document_id,
                    ],
                )
                row = cur.fetchone()

            if not row:
                return None

            return SourceDocument(
                id=document_id,
                ingestion_run_id=row[0],
                documento_id_externo=row[1],
                arquivo_origem=row[2],
                arquivo_nome=row[3],
                pasta_origem=row[4],
                bloco_logico=row[5],
                hash_sha256=row[6],
                extensao=row[7],
                tamanho_bytes=row[8],
                texto_extraido=texto_extraido,
                extracao_status=extracao_status,
                extracao_metodo=extracao_metodo,
                created_at=row[9],
                updated_at=updated_at,
            )

        return self._commit_or_rollback(_action)

    def update_document_classification(
        self,
        document_id: UUID,
        ramo: str,
        fonte_tipo: str,
        autoridade: str,
        peso_confianca: str,
        tem_anotacao: bool = False,
        tem_atencao_documento: bool = False,
        ano: Optional[int] = None,
        banca: Optional[str] = None,
        subtema: Optional[str] = None,
        tipo: Optional[str] = None,
        status_documento: Optional[str] = None,
        motivo_status: Optional[str] = None,
    ) -> Optional[SourceDocument]:
        """Atualiza classificacao de um documento."""
        if not self.enabled:
            return None

        updated_at = datetime.now(timezone.utc)

        def _action() -> Optional[SourceDocument]:
            with self.conn.cursor() as cur:
                cur.execute(
                    sql.SQL(
                        """
                        UPDATE {}.source_documents
                        SET ramo = %s, fonte_tipo = %s, autoridade = %s,
                            peso_confianca = %s, tem_anotacao = %s, tem_atencao_documento = %s,
                            ano = %s, banca = %s, subtema = %s, tipo = %s,
                            status_documento = COALESCE(%s, status_documento),
                            motivo_status = %s,
                            updated_at = %s
                        WHERE id = %s
                        RETURNING ingestion_run_id, documento_id_externo, arquivo_origem,
                                  arquivo_nome, pasta_origem, bloco_logico, hash_sha256,
                                  extensao, tamanho_bytes, texto_extraido, extracao_status,
                                  ramo, fonte_tipo, autoridade, peso_confianca, tem_anotacao,
                                  tem_atencao_documento, ano, banca, subtema, tipo,
                                  status_documento, motivo_status, created_at
                        """
                    ).format(sql.Identifier(SCHEMA_JURIDICO)),
                    [
                        ramo,
                        fonte_tipo,
                        autoridade,
                        peso_confianca,
                        tem_anotacao,
                        tem_atencao_documento,
                        ano,
                        banca,
                        subtema,
                        tipo,
                        status_documento,
                        motivo_status,
                        updated_at,
                        document_id,
                    ],
                )
                row = cur.fetchone()

            if not row:
                return None

            return SourceDocument(
                id=document_id,
                ingestion_run_id=row[0],
                documento_id_externo=row[1],
                arquivo_origem=row[2],
                arquivo_nome=row[3],
                pasta_origem=row[4],
                bloco_logico=row[5],
                hash_sha256=row[6],
                extensao=row[7],
                tamanho_bytes=row[8],
                texto_extraido=row[9],
                extracao_status=row[10],
                ramo=row[11],
                fonte_tipo=row[12],
                autoridade=row[13],
                peso_confianca=row[14],
                tem_anotacao=row[15],
                tem_atencao_documento=row[16],
                ano=row[17],
                banca=row[18],
                subtema=row[19],
                tipo=row[20],
                status_documento=row[21],
                motivo_status=row[22],
                created_at=row[23],
                updated_at=updated_at,
            )

        return self._commit_or_rollback(_action)

    # ─────────────────────────────────────────────────────────────────────────
    # DOCUMENT CHUNKS
    # ─────────────────────────────────────────────────────────────────────────

    def save_chunk(
        self,
        ingestion_run_id: UUID,
        source_document_id: UUID,
        chunk_id_externo: str,
        ordem_chunk: int,
        texto_chunk: str,
        ramo: str,
        bloco_logico: str,
        fonte_tipo: str,
        autoridade: str,
        arquivo_origem: str,
        pasta_origem: str,
        peso_confianca: str,
        prioridade_recuperacao: float,
        titulo_secao: Optional[str] = None,
        artigo_ref: Optional[str] = None,
        tem_anotacao: bool = False,
        tem_atencao: bool = False,
        tipo_marcacao: Optional[str] = None,
        relevancia_estudo: Optional[str] = None,
        ano: Optional[int] = None,
        banca: Optional[str] = None,
        subtema: Optional[str] = None,
        tipo: Optional[str] = None,
    ) -> DocumentChunk:
        """Salva um chunk de documento."""
        if not self.enabled:
            return DocumentChunk(
                ingestion_run_id=ingestion_run_id,
                source_document_id=source_document_id,
                chunk_id_externo=chunk_id_externo,
                ordem_chunk=ordem_chunk,
                texto_chunk=texto_chunk,
                ramo=ramo,
                bloco_logico=bloco_logico,
                fonte_tipo=fonte_tipo,
                autoridade=autoridade,
                arquivo_origem=arquivo_origem,
                pasta_origem=pasta_origem,
                peso_confianca=peso_confianca,
                prioridade_recuperacao=prioridade_recuperacao,
                titulo_secao=titulo_secao,
                artigo_ref=artigo_ref,
                tem_anotacao=tem_anotacao,
                tem_atencao=tem_atencao,
                tipo_marcacao=tipo_marcacao,
                relevancia_estudo=relevancia_estudo,
                ano=ano,
                banca=banca,
                subtema=subtema,
                tipo=tipo,
            )

        def _action() -> DocumentChunk:
            with self.conn.cursor() as cur:
                cur.execute(
                    sql.SQL(
                        """
                        INSERT INTO {}.document_chunks
                        (ingestion_run_id, source_document_id, chunk_id_externo, ordem_chunk,
                         texto_chunk, ramo, bloco_logico, fonte_tipo, autoridade,
                         arquivo_origem, pasta_origem, peso_confianca, prioridade_recuperacao,
                         titulo_secao, artigo_ref, tem_anotacao, tem_atencao,
                         tipo_marcacao, relevancia_estudo, ano, banca, subtema, tipo)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id, created_at
                        """
                    ).format(sql.Identifier(SCHEMA_JURIDICO)),
                    [
                        ingestion_run_id,
                        source_document_id,
                        chunk_id_externo,
                        ordem_chunk,
                        texto_chunk,
                        ramo,
                        bloco_logico,
                        fonte_tipo,
                        autoridade,
                        arquivo_origem,
                        pasta_origem,
                        peso_confianca,
                        prioridade_recuperacao,
                        titulo_secao,
                        artigo_ref,
                        tem_anotacao,
                        tem_atencao,
                        tipo_marcacao,
                        relevancia_estudo,
                        ano,
                        banca,
                        subtema,
                        tipo,
                    ],
                )
                row = cur.fetchone()

            return DocumentChunk(
                id=row[0],
                ingestion_run_id=ingestion_run_id,
                source_document_id=source_document_id,
                chunk_id_externo=chunk_id_externo,
                ordem_chunk=ordem_chunk,
                texto_chunk=texto_chunk,
                ramo=ramo,
                bloco_logico=bloco_logico,
                fonte_tipo=fonte_tipo,
                autoridade=autoridade,
                arquivo_origem=arquivo_origem,
                pasta_origem=pasta_origem,
                peso_confianca=peso_confianca,
                prioridade_recuperacao=prioridade_recuperacao,
                titulo_secao=titulo_secao,
                artigo_ref=artigo_ref,
                tem_anotacao=tem_anotacao,
                tem_atencao=tem_atencao,
                tipo_marcacao=tipo_marcacao,
                relevancia_estudo=relevancia_estudo,
                ano=ano,
                banca=banca,
                subtema=subtema,
                tipo=tipo,
                created_at=row[1],
            )

        return self._commit_or_rollback(_action)

    # ─────────────────────────────────────────────────────────────────────────
    # RETRIEVAL EVAL
    # ─────────────────────────────────────────────────────────────────────────

    def save_eval_result(
        self,
        ingestion_run_id: UUID,
        bloco_logico: str,
        query: str,
        tipo_teste: str,
        top_k_json: Optional[Dict[str, Any]],
        resultado: str,
        observacao: Optional[str] = None,
    ) -> RetrievalEvalRun:
        """Salva resultado de teste de recuperacao."""
        if not self.enabled:
            return RetrievalEvalRun(
                ingestion_run_id=ingestion_run_id,
                bloco_logico=bloco_logico,
                query=query,
                tipo_teste=tipo_teste,
                top_k_json=top_k_json,
                resultado=resultado,
                observacao=observacao,
            )

        def _action() -> RetrievalEvalRun:
            with self.conn.cursor() as cur:
                cur.execute(
                    sql.SQL(
                        """
                        INSERT INTO {}.retrieval_eval_runs
                        (ingestion_run_id, bloco_logico, query, tipo_teste, top_k_json,
                         resultado, observacao)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id, created_at
                        """
                    ).format(sql.Identifier(SCHEMA_JURIDICO)),
                    [
                        ingestion_run_id,
                        bloco_logico,
                        query,
                        tipo_teste,
                        json.dumps(top_k_json) if top_k_json else None,
                        resultado,
                        observacao,
                    ],
                )
                row = cur.fetchone()

            return RetrievalEvalRun(
                id=row[0],
                ingestion_run_id=ingestion_run_id,
                bloco_logico=bloco_logico,
                query=query,
                tipo_teste=tipo_teste,
                top_k_json=top_k_json,
                resultado=resultado,
                observacao=observacao,
                created_at=row[1],
            )

        return self._commit_or_rollback(_action)

    # ─────────────────────────────────────────────────────────────────────────
    # QUARANTINE
    # ─────────────────────────────────────────────────────────────────────────

    def move_document_to_quarantine(
        self,
        source_document_id: UUID,
        motivo: str,
        detalhes: Optional[str] = None,
        needs_review: bool = True,
    ) -> DocumentQuarantine:
        """Move documento para quarentena."""
        if not self.enabled:
            return DocumentQuarantine(
                source_document_id=source_document_id,
                motivo=motivo,
                detalhes=detalhes,
                needs_review=needs_review,
            )

        updated_at = datetime.now(timezone.utc)

        def _action() -> DocumentQuarantine:
            with self.conn.cursor() as cur:
                cur.execute(
                    sql.SQL(
                        """
                        UPDATE {}.source_documents
                        SET status_documento = %s, motivo_status = %s, updated_at = %s
                        WHERE id = %s
                        """
                    ).format(sql.Identifier(SCHEMA_JURIDICO)),
                    [
                        StatusDocumento.QUARENTENA.value,
                        motivo,
                        updated_at,
                        source_document_id,
                    ],
                )

                cur.execute(
                    sql.SQL(
                        """
                        INSERT INTO {}.document_quarantine
                        (source_document_id, motivo, detalhes, needs_review)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id, created_at
                        """
                    ).format(sql.Identifier(SCHEMA_JURIDICO)),
                    [source_document_id, motivo, detalhes, needs_review],
                )
                row = cur.fetchone()

            return DocumentQuarantine(
                id=row[0],
                source_document_id=source_document_id,
                motivo=motivo,
                detalhes=detalhes,
                needs_review=needs_review,
                created_at=row[1],
            )

        return self._commit_or_rollback(_action)

    def update_quarantine_review(
        self,
        quarantine_id: UUID,
        review_status: StatusReview,
    ) -> Optional[DocumentQuarantine]:
        """Atualiza status de revisao de documento em quarentena."""
        if not self.enabled:
            return None

        reviewed_at = datetime.now(timezone.utc)

        def _action() -> Optional[DocumentQuarantine]:
            with self.conn.cursor() as cur:
                cur.execute(
                    sql.SQL(
                        """
                        UPDATE {}.document_quarantine
                        SET review_status = %s, reviewed_at = %s
                        WHERE id = %s
                        RETURNING source_document_id, motivo, detalhes, needs_review, created_at
                        """
                    ).format(sql.Identifier(SCHEMA_JURIDICO)),
                    [review_status.value, reviewed_at, quarantine_id],
                )
                row = cur.fetchone()

            if not row:
                return None

            return DocumentQuarantine(
                id=quarantine_id,
                source_document_id=row[0],
                motivo=row[1],
                detalhes=row[2],
                needs_review=row[3],
                review_status=review_status,
                created_at=row[4],
                reviewed_at=reviewed_at,
            )

        return self._commit_or_rollback(_action)
