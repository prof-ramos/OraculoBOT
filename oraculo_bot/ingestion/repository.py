"""Camada de persistencia para o pipeline de ingestao RAG Lote 1.

Implementa o repositorio conforme especificado em:
- docs/RAG_LOTE1/PASSO_5_ESPECIFICACAO_IMPLEMENTACAO.md
- docs/RAG_LOTE1/IMPLEMENTATION_TODO.md (EPIC 1, Tarefa 1.3)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID

import psycopg
from psycopg import sql

from oraculo_bot.config import SUPABASE_DB_URL
from oraculo_bot.ingestion.models import (
    IngestionRun,
    SourceDocument,
    DocumentChunk,
    RetrievalEvalRun,
    DocumentQuarantine,
    StatusIngestaoRun,
    StatusDocumento,
    StatusReview,
)

logger = logging.getLogger(__name__)

SCHEMA_JURIDICO = "juridico"


class IngestionRepository:
    """Repositorio para operacoes de persistencia do pipeline de ingestao.

    Centraliza todas as operacoes de banco de dados relacionadas ao pipeline RAG.
    Usa psycopg direto para compatibilidade com o resto do projeto.
    """

    def __init__(self, db_url: Optional[str] = None):
        """Inicializa o repositorio.

        Args:
            db_url: URL de conexao PostgreSQL. Se None, usa SUPABASE_DB_URL.
                Se string vazia, desabilita explicitamente a persistencia.
        """
        self.db_url = SUPABASE_DB_URL if db_url is None else db_url
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
        """Cria uma nova rodada de ingestao.

        Args:
            run_key: Chave unica da rodada (ex: lote1_v1_eleitoral).
            lote: Identificador do lote (ex: lote1).
            bloco_logico: Bloco logico sendo processado (ex: eleitoral).
            pasta_origem: Caminho da pasta fisica de origem.
            created_by: Identificador de quem criou a rodada.
            observacoes: Observacoes opcionais.

        Returns:
            IngestionRun criada.
        """
        if not self.enabled:
            # Fallback: retorna objeto sem persistir
            return IngestionRun(
                run_key=run_key,
                lote=lote,
                bloco_logico=bloco_logico,
                pasta_origem=pasta_origem,
                status=StatusIngestaoRun.RUNNING,
                started_at=datetime.now(timezone.utc),
                created_by=created_by,
                observacoes=observacoes,
            )

        with self.conn.cursor() as cur:
            cur.execute(
                sql.SQL("""
                    INSERT INTO {}.ingestion_runs
                    (run_key, lote, bloco_logico, pasta_origem, status, started_at, created_by, observacoes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, created_at
                """).format(sql.Identifier(SCHEMA_JURIDICO)),
                [
                    run_key,
                    lote,
                    bloco_logico,
                    pasta_origem,
                    StatusIngestaoRun.RUNNING.value,
                    datetime.now(timezone.utc),
                    created_by,
                    observacoes,
                ],
            )
            row = cur.fetchone()
            self.conn.commit()

            return IngestionRun(
                id=row[0],
                run_key=run_key,
                lote=lote,
                bloco_logico=bloco_logico,
                pasta_origem=pasta_origem,
                status=StatusIngestaoRun.RUNNING,
                started_at=datetime.now(timezone.utc),
                created_by=created_by,
                observacoes=observacoes,
                ramo=ramo or SourceDocument.ramo,
                fonte_tipo=fonte_tipo or SourceDocument.fonte_tipo,
                autoridade=autoridade or SourceDocument.autoridade,
                peso_confianca=peso_confianca or SourceDocument.peso_confianca,
                created_at=row[1],
            )

    def finalize_ingestion_run(
        self,
        run_id: UUID,
        status: StatusIngestaoRun,
        stats_json: Optional[Dict[str, Any]] = None,
    ) -> Optional[IngestionRun]:
        """Finaliza uma rodada de ingestao.

        Args:
            run_id: UUID da rodada.
            status: Status final (validated, failed, rolled_back).
            stats_json: Estatisticas da rodada.

        Returns:
            IngestionRun atualizada ou None se nao encontrada.
        """
        if not self.enabled:
            return None

        with self.conn.cursor() as cur:
            cur.execute(
                sql.SQL("""
                    UPDATE {}.ingestion_runs
                    SET status = %s, finished_at = %s, stats_json = %s
                    WHERE id = %s
                    RETURNING run_key, lote, bloco_logico, pasta_origem, started_at,
                              created_by, observacoes, created_at
                """).format(sql.Identifier(SCHEMA_JURIDICO)),
                [
                    status.value,
                    datetime.now(timezone.utc),
                    json.dumps(stats_json) if stats_json else None,
                    run_id,
                ],
            )
            row = cur.fetchone()
            self.conn.commit()

            if row:
                return IngestionRun(
                    id=run_id,
                    run_key=row[0],
                    lote=row[1],
                    bloco_logico=row[2],
                    pasta_origem=row[3],
                    status=status,
                    started_at=row[4],
                    finished_at=datetime.now(timezone.utc),
                    created_by=row[5],
                    observacoes=row[6],
                    stats_json=stats_json,
                    created_at=row[7],
                )
            return None

    def get_ingestion_run_by_key(self, run_key: str) -> Optional[IngestionRun]:
        """Busca uma rodada de ingestao pela chave.

        Args:
            run_key: Chave unica da rodada.

        Returns:
            IngestionRun ou None se nao encontrada.
        """
        if not self.enabled:
            return None

        with self.conn.cursor() as cur:
            cur.execute(
                sql.SQL("""
                    SELECT id, run_key, lote, bloco_logico, pasta_origem, status,
                           started_at, finished_at, created_by, observacoes,
                           stats_json, created_at
                    FROM {}.ingestion_runs
                    WHERE run_key = %s
                """).format(sql.Identifier(SCHEMA_JURIDICO)),
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
        """Registra um novo documento fonte.

        Args:
            ingestion_run_id: UUID da rodada de ingestao.
            documento_id_externo: Identificador unico do documento.
            arquivo_origem: Caminho completo do arquivo.
            arquivo_nome: Nome do arquivo.
            pasta_origem: Pasta fisica de origem.
            bloco_logico: Bloco logico inferido.
            hash_sha256: Hash SHA-256 do arquivo.
            extensao: Extensao do arquivo.
            tamanho_bytes: Tamanho em bytes.

        Returns:
            SourceDocument criado.
        """
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
            )

        with self.conn.cursor() as cur:
            cur.execute(
                sql.SQL("""
                    INSERT INTO {}.source_documents
                    (ingestion_run_id, documento_id_externo, arquivo_origem, arquivo_nome,
                     pasta_origem, bloco_logico, hash_sha256, extensao, tamanho_bytes, ramo, fonte_tipo, autoridade, peso_confianca)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, created_at
                """).format(sql.Identifier(SCHEMA_JURIDICO)),
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
            self.conn.commit()

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

    def update_document_extraction(
        self,
        document_id: UUID,
        texto_extraido: Optional[str],
        extracao_status: str,
        extracao_metodo: Optional[str] = None,
    ) -> Optional[SourceDocument]:
        """Atualiza dados de extracao de um documento.

        Args:
            document_id: UUID do documento.
            texto_extraido: Texto extraido (pode ser None se falhou).
            extracao_status: Status da extracao (ok, parcial, falha).
            extracao_metodo: Metodo usado para extracao.

        Returns:
            SourceDocument atualizado ou None se nao encontrado.
        """
        if not self.enabled:
            return None

        with self.conn.cursor() as cur:
            cur.execute(
                sql.SQL("""
                    UPDATE {}.source_documents
                    SET texto_extraido = %s, extracao_status = %s,
                        extracao_metodo = %s, updated_at = %s
                    WHERE id = %s
                    RETURNING ingestion_run_id, documento_id_externo, arquivo_origem,
                              arquivo_nome, pasta_origem, bloco_logico, hash_sha256,
                              extensao, tamanho_bytes, created_at
                """).format(sql.Identifier(SCHEMA_JURIDICO)),
                [
                    texto_extraido,
                    extracao_status,
                    extracao_metodo,
                    datetime.now(timezone.utc),
                    document_id,
                ],
            )
            row = cur.fetchone()
            self.conn.commit()

            if row:
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
                )
            return None

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
        """Atualiza classificacao de um documento.

        Args:
            document_id: UUID do documento.
            ramo: Ramo juridico.
            fonte_tipo: Tipo de fonte.
            autoridade: Autoridade emissora.
            peso_confianca: Nivel de confianca (alto, medio, baixo).
            tem_anotacao: Se tem anotacoes.
            tem_atencao_documento: Se tem marcacao #Atencao.
            ano: Ano do documento.
            banca: Banca examinadora (se questao).
            subtema: Subtema especifico.
            tipo: Tipo adicional.
            status_documento: Status do documento.
            motivo_status: Motivo do status (se quarentena/revision).

        Returns:
            SourceDocument atualizado ou None.
        """
        if not self.enabled:
            return None

        with self.conn.cursor() as cur:
            cur.execute(
                sql.SQL("""
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
                """).format(sql.Identifier(SCHEMA_JURIDICO)),
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
                    datetime.now(timezone.utc),
                    document_id,
                ],
            )
            row = cur.fetchone()
            self.conn.commit()

            if row:
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
                )
            return None

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
        """Salva um chunk de documento.

        Args:
            ingestion_run_id: UUID da rodada.
            source_document_id: UUID do documento fonte.
            chunk_id_externo: Identificador unico do chunk.
            ordem_chunk: Ordem do chunk no documento.
            texto_chunk: Texto do chunk.
            ramo: Ramo juridico.
            bloco_logico: Bloco logico.
            fonte_tipo: Tipo de fonte.
            autoridade: Autoridade.
            arquivo_origem: Arquivo de origem.
            pasta_origem: Pasta de origem.
            peso_confianca: Nivel de confianca.
            prioridade_recuperacao: Score de prioridade.
            titulo_secao: Titulo da secao (se houver).
            artigo_ref: Referencia de artigo (se houver).
            tem_anotacao: Se tem anotacao.
            tem_atencao: Se tem marcacao #Atencao.
            tipo_marcacao: Tipo de marcacao.
            relevancia_estudo: Relevancia para estudo.
            ano: Ano.
            banca: Banca.
            subtema: Subtema.
            tipo: Tipo.

        Returns:
            DocumentChunk salvo.
        """
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

        with self.conn.cursor() as cur:
            cur.execute(
                sql.SQL("""
                    INSERT INTO {}.document_chunks
                    (ingestion_run_id, source_document_id, chunk_id_externo, ordem_chunk,
                     texto_chunk, ramo, bloco_logico, fonte_tipo, autoridade,
                     arquivo_origem, pasta_origem, peso_confianca, prioridade_recuperacao,
                     titulo_secao, artigo_ref, tem_anotacao, tem_atencao,
                     tipo_marcacao, relevancia_estudo, ano, banca, subtema, tipo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, created_at
                """).format(sql.Identifier(SCHEMA_JURIDICO)),
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
            self.conn.commit()

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
        """Salva resultado de teste de recuperacao.

        Args:
            ingestion_run_id: UUID da rodada.
            bloco_logico: Bloco logico testado.
            query: Query de teste.
            tipo_teste: Tipo de teste (canonica, autoridade, contaminacao, atencao).
            top_k_json: Top-k resultados como JSON.
            resultado: Resultado (pass, warning, fail).
            observacao: Observacao opcional.

        Returns:
            RetrievalEvalRun salvo.
        """
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

        with self.conn.cursor() as cur:
            cur.execute(
                sql.SQL("""
                    INSERT INTO {}.retrieval_eval_runs
                    (ingestion_run_id, bloco_logico, query, tipo_teste, top_k_json,
                     resultado, observacao)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, created_at
                """).format(sql.Identifier(SCHEMA_JURIDICO)),
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
            self.conn.commit()

            return RetrievalEvalRun(
                id=row[0],
                ingestion_run_id=ingestion_run_id,
                bloco_logico=bloco_logico,
                query=query,
                tipo_teste=tipo_teste,
                top_k_json=top_k_json,
                resultado=resultado,
                observacao=observacao,
                ramo=ramo or SourceDocument.ramo,
                fonte_tipo=fonte_tipo or SourceDocument.fonte_tipo,
                autoridade=autoridade or SourceDocument.autoridade,
                peso_confianca=peso_confianca or SourceDocument.peso_confianca,
                created_at=row[1],
            )

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
        """Move documento para quarentena.

        Args:
            source_document_id: UUID do documento.
            motivo: Motivo da quarentena.
            detalhes: Detalhes adicionais.
            needs_review: Se precisa revisao manual.

        Returns:
            DocumentQuarantine criado.
        """
        if not self.enabled:
            return DocumentQuarantine(
                source_document_id=source_document_id,
                motivo=motivo,
                detalhes=detalhes,
                needs_review=needs_review,
            )

        with self.conn.cursor() as cur:
            # Atualiza status do documento
            cur.execute(
                sql.SQL("""
                    UPDATE {}.source_documents
                    SET status_documento = %s, motivo_status = %s, updated_at = %s
                    WHERE id = %s
                """).format(sql.Identifier(SCHEMA_JURIDICO)),
                [
                    StatusDocumento.QUARENTENA.value,
                    motivo,
                    datetime.now(timezone.utc),
                    source_document_id,
                ],
            )

            # Cria registro na quarentena
            cur.execute(
                sql.SQL("""
                    INSERT INTO {}.document_quarantine
                    (source_document_id, motivo, detalhes, needs_review)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, created_at
                """).format(sql.Identifier(SCHEMA_JURIDICO)),
                [source_document_id, motivo, detalhes, needs_review],
            )
            row = cur.fetchone()
            self.conn.commit()

            return DocumentQuarantine(
                id=row[0],
                source_document_id=source_document_id,
                motivo=motivo,
                detalhes=detalhes,
                needs_review=needs_review,
                ramo=ramo or SourceDocument.ramo,
                fonte_tipo=fonte_tipo or SourceDocument.fonte_tipo,
                autoridade=autoridade or SourceDocument.autoridade,
                peso_confianca=peso_confianca or SourceDocument.peso_confianca,
                created_at=row[1],
            )

    def update_quarantine_review(
        self,
        quarantine_id: UUID,
        review_status: StatusReview,
    ) -> Optional[DocumentQuarantine]:
        """Atualiza status de revisao de documento em quarentena.

        Args:
            quarantine_id: UUID do registro de quarentena.
            review_status: Novo status de revisao.

        Returns:
            DocumentQuarantine atualizado ou None.
        """
        if not self.enabled:
            return None

        with self.conn.cursor() as cur:
            cur.execute(
                sql.SQL("""
                    UPDATE {}.document_quarantine
                    SET review_status = %s, reviewed_at = %s
                    WHERE id = %s
                    RETURNING source_document_id, motivo, detalhes, needs_review, created_at
                """).format(sql.Identifier(SCHEMA_JURIDICO)),
                [review_status.value, datetime.now(timezone.utc), quarantine_id],
            )
            row = cur.fetchone()
            self.conn.commit()

            if row:
                return DocumentQuarantine(
                    id=quarantine_id,
                    source_document_id=row[0],
                    motivo=row[1],
                    detalhes=row[2],
                    needs_review=row[3],
                    review_status=review_status,
                    created_at=row[4],
                    reviewed_at=datetime.now(timezone.utc),
                )
            return None
