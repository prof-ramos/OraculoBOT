"""Testes unitarios basicos para o repositorio de ingestao."""

from oraculo_bot.ingestion.models import StatusIngestaoRun, StatusDocumento
from oraculo_bot.ingestion.repository import IngestionRepository


class TestIngestionRepositoryWithoutDb:
    def test_disabled_without_db_url(self):
        repo = IngestionRepository(db_url="")
        assert repo.enabled is False

    def test_create_ingestion_run_fallback(self):
        repo = IngestionRepository(db_url="")
        run = repo.create_ingestion_run(
            run_key="lote1_v1_eleitoral",
            lote="lote1",
            bloco_logico="eleitoral",
            pasta_origem="/data/eleitoral",
            created_by="test",
        )
        assert run.run_key == "lote1_v1_eleitoral"
        assert run.status == StatusIngestaoRun.RUNNING
        assert run.bloco_logico == "eleitoral"

    def test_register_source_document_fallback(self):
        repo = IngestionRepository(db_url="")
        doc = repo.register_source_document(
            ingestion_run_id=None,
            documento_id_externo="doc_001",
            arquivo_origem="/data/test.pdf",
            arquivo_nome="test.pdf",
            pasta_origem="/data",
            bloco_logico="eleitoral",
            hash_sha256="abc123",
            extensao="pdf",
            tamanho_bytes=1234,
        )
        assert doc.documento_id_externo == "doc_001"
        assert doc.arquivo_nome == "test.pdf"
        assert doc.bloco_logico == "eleitoral"

    def test_save_chunk_fallback(self):
        repo = IngestionRepository(db_url="")
        chunk = repo.save_chunk(
            ingestion_run_id=None,
            source_document_id=None,
            chunk_id_externo="chunk_001",
            ordem_chunk=1,
            texto_chunk="Art. 1o teste",
            ramo="eleitoral",
            bloco_logico="eleitoral",
            fonte_tipo="lei",
            autoridade="planalto",
            arquivo_origem="/data/test.pdf",
            pasta_origem="/data",
            peso_confianca="alto",
            prioridade_recuperacao=140.0,
        )
        assert chunk.chunk_id_externo == "chunk_001"
        assert chunk.prioridade_recuperacao == 140.0
        assert chunk.bloco_logico == "eleitoral"

    def test_save_eval_result_fallback(self):
        repo = IngestionRepository(db_url="")
        result = repo.save_eval_result(
            ingestion_run_id=None,
            bloco_logico="eleitoral",
            query="voto obrigatorio",
            tipo_teste="canonica",
            top_k_json={"top": ["c1"]},
            resultado="pass",
            observacao="ok",
        )
        assert result.bloco_logico == "eleitoral"
        assert result.resultado.value == "pass"

    def test_move_document_to_quarantine_fallback(self):
        repo = IngestionRepository(db_url="")
        quarantine = repo.move_document_to_quarantine(
            source_document_id=None,
            motivo="extracao_ruim",
            detalhes="texto vazio",
        )
        assert quarantine.motivo == "extracao_ruim"
        assert quarantine.detalhes == "texto vazio"

    def test_finalize_without_db_returns_none(self):
        repo = IngestionRepository(db_url="")
        result = repo.finalize_ingestion_run(run_id=None, status=StatusIngestaoRun.VALIDATED)
        assert result is None

    def test_update_without_db_returns_none(self):
        repo = IngestionRepository(db_url="")
        assert repo.update_document_extraction(document_id=None, texto_extraido="x", extracao_status="ok") is None
        assert repo.update_document_classification(
            document_id=None,
            ramo="eleitoral",
            fonte_tipo="lei",
            autoridade="planalto",
            peso_confianca="alto",
            status_documento=StatusDocumento.APROVADO.value,
        ) is None
