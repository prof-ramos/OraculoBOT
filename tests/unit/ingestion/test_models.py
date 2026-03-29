"""Testes unitarios para models.py - Pipeline de ingestao RAG Lote 1."""

from datetime import datetime, timezone

from oraculo_bot.ingestion.models import (
    RamoJuridico,
    FonteTipo,
    Autoridade,
    PesoConfianca,
    StatusDocumento,
    StatusIngestaoRun,
    StatusExtracao,
    StatusValidacao,
    StatusEmbedding,
    TipoTesteRetrieval,
    ResultadoTeste,
    StatusReview,
    IngestionRun,
    SourceDocument,
    DocumentChunk,
    RetrievalEvalRun,
    DocumentQuarantine,
    calcular_prioridade_recuperacao,
    PESO_CONFIANCA_SCORE,
    FONTE_TIPO_SCORE,
    AUTORIDADE_SCORE,
)


class TestEnums:
    def test_ramo_juridico_values(self):
        ramos = [r.value for r in RamoJuridico]
        assert "eleitoral" in ramos
        assert "administrativo" in ramos
        assert "penal" in ramos
        assert "constitucional" in ramos

    def test_fonte_tipo_values(self):
        tipos = [t.value for t in FonteTipo]
        assert "lei" in tipos
        assert "resolucao" in tipos
        assert "doutrina" in tipos
        assert "convencao" in tipos

    def test_autoridade_values(self):
        autoridades = [a.value for a in Autoridade]
        assert "planalto" in autoridades
        assert "stf" in autoridades
        assert "tse" in autoridades
        assert "desconhecida" in autoridades

    def test_status_ingestao_run_values(self):
        status = [s.value for s in StatusIngestaoRun]
        assert {"planned", "running", "validated", "failed", "rolled_back"}.issubset(status)

    def test_status_documento_values(self):
        status = [s.value for s in StatusDocumento]
        assert {"aprovado", "quarentena", "descartado", "revisao_manual"}.issubset(status)


class TestIngestionRun:
    def test_create_minimal(self):
        run = IngestionRun(run_key="lote1_v1_eleitoral")
        assert run.run_key == "lote1_v1_eleitoral"
        assert run.status == StatusIngestaoRun.PLANNED
        assert run.lote == "lote1"
        assert isinstance(run.created_at, datetime)

    def test_create_with_all_fields(self):
        run = IngestionRun(
            run_key="lote1_v2_administrativo",
            lote="lote1",
            bloco_logico="administrativo",
            pasta_origem="/data/administrativo",
            status=StatusIngestaoRun.RUNNING,
            started_at=datetime.now(timezone.utc),
            created_by="test_user",
            observacoes="Teste de ingestao",
        )
        assert run.bloco_logico == "administrativo"
        assert run.pasta_origem == "/data/administrativo"
        assert run.status == StatusIngestaoRun.RUNNING
        assert run.created_by == "test_user"

    def test_status_from_string(self):
        run = IngestionRun(run_key="test", status="running")
        assert run.status == StatusIngestaoRun.RUNNING


class TestSourceDocument:
    def test_create_minimal(self):
        doc = SourceDocument(documento_id_externo="doc_001", arquivo_nome="test.pdf", hash_sha256="abc123")
        assert doc.documento_id_externo == "doc_001"
        assert doc.arquivo_nome == "test.pdf"
        assert doc.hash_sha256 == "abc123"
        assert doc.extracao_status == StatusExtracao.OK
        assert doc.status_documento == StatusDocumento.APROVADO

    def test_create_with_classification(self):
        doc = SourceDocument(
            documento_id_externo="lei_123",
            arquivo_nome="lei_123.pdf",
            hash_sha256="def456",
            ramo=RamoJuridico.ELEITORAL,
            fonte_tipo=FonteTipo.LEI,
            autoridade=Autoridade.PLANALTO,
            peso_confianca=PesoConfianca.ALTO,
        )
        assert doc.ramo == RamoJuridico.ELEITORAL
        assert doc.fonte_tipo == FonteTipo.LEI
        assert doc.autoridade == Autoridade.PLANALTO
        assert doc.peso_confianca == PesoConfianca.ALTO

    def test_enums_from_strings(self):
        doc = SourceDocument(
            documento_id_externo="test",
            arquivo_nome="test.pdf",
            hash_sha256="abc",
            ramo="constitucional",
            fonte_tipo="resolucao",
            autoridade="stf",
            extracao_status="parcial",
            status_documento="quarentena",
        )
        assert doc.ramo == RamoJuridico.CONSTITUCIONAL
        assert doc.fonte_tipo == FonteTipo.RESOLUCAO
        assert doc.autoridade == Autoridade.STF
        assert doc.extracao_status == StatusExtracao.PARCIAL
        assert doc.status_documento == StatusDocumento.QUARENTENA


class TestDocumentChunk:
    def test_create_minimal(self):
        chunk = DocumentChunk(chunk_id_externo="chunk_001", texto_chunk="Texto do chunk de teste")
        assert chunk.chunk_id_externo == "chunk_001"
        assert chunk.texto_chunk == "Texto do chunk de teste"
        assert chunk.status_validacao == StatusValidacao.PENDENTE
        assert chunk.embedding_status == StatusEmbedding.PENDENTE

    def test_create_with_all_fields(self):
        chunk = DocumentChunk(
            chunk_id_externo="chunk_002",
            ordem_chunk=1,
            texto_chunk="Art. 1o ...",
            titulo_secao="CAPITULO I",
            artigo_ref="Art. 1o",
            ramo=RamoJuridico.CONSTITUCIONAL,
            bloco_logico="constitucional",
            fonte_tipo=FonteTipo.LEI,
            autoridade=Autoridade.PLANALTO,
            arquivo_origem="/data/cf.pdf",
            pasta_origem="/data",
            tem_atencao=True,
            tipo_marcacao="atencao",
            relevancia_estudo="alta",
            peso_confianca=PesoConfianca.ALTO,
            prioridade_recuperacao=150.0,
        )
        assert chunk.titulo_secao == "CAPITULO I"
        assert chunk.artigo_ref == "Art. 1o"
        assert chunk.tem_atencao is True
        assert chunk.prioridade_recuperacao == 150.0

    def test_enums_from_strings(self):
        chunk = DocumentChunk(
            chunk_id_externo="test",
            texto_chunk="test",
            ramo="penal",
            fonte_tipo="doutrina",
            autoridade="banca",
            peso_confianca="baixo",
            status_validacao="aprovado",
            embedding_status="gerado",
        )
        assert chunk.ramo == RamoJuridico.PENAL
        assert chunk.fonte_tipo == FonteTipo.DOCTRINA
        assert chunk.autoridade == Autoridade.BANCA
        assert chunk.peso_confianca == PesoConfianca.BAIXO
        assert chunk.status_validacao == StatusValidacao.APROVADO
        assert chunk.embedding_status == StatusEmbedding.GERADO


class TestRetrievalEvalRun:
    def test_create_minimal(self):
        eval_run = RetrievalEvalRun(query="Qual a competencia da Uniao?")
        assert eval_run.query == "Qual a competencia da Uniao?"
        assert eval_run.tipo_teste == TipoTesteRetrieval.CANONICA
        assert eval_run.resultado == ResultadoTeste.WARNING

    def test_create_with_all_fields(self):
        eval_run = RetrievalEvalRun(
            bloco_logico="eleitoral",
            query="O que e voto obrigatorio?",
            tipo_teste=TipoTesteRetrieval.AUTORIDADE,
            top_k_json={"chunks": ["c1", "c2"]},
            resultado=ResultadoTeste.PASS,
            observacao="Teste passou",
        )
        assert eval_run.bloco_logico == "eleitoral"
        assert eval_run.tipo_teste == TipoTesteRetrieval.AUTORIDADE
        assert eval_run.top_k_json == {"chunks": ["c1", "c2"]}
        assert eval_run.resultado == ResultadoTeste.PASS


class TestDocumentQuarantine:
    def test_create_minimal(self):
        quarantine = DocumentQuarantine(motivo="extracao_ruim")
        assert quarantine.motivo == "extracao_ruim"
        assert quarantine.needs_review is True
        assert quarantine.review_status == StatusReview.PENDENTE

    def test_create_with_all_fields(self):
        quarantine = DocumentQuarantine(
            motivo="classificacao_ambigua",
            detalhes="Documento pode ser constitucional ou administrativo",
            needs_review=True,
        )
        assert quarantine.motivo == "classificacao_ambigua"
        assert "constitucional" in quarantine.detalhes


class TestCalcularPrioridadeRecuperacao:
    def test_score_base_alto(self):
        score = calcular_prioridade_recuperacao(PesoConfianca.ALTO, FonteTipo.MATERIAL_APOIO, Autoridade.DESCONHECIDA)
        assert score == 92.0

    def test_score_base_medio(self):
        score = calcular_prioridade_recuperacao(PesoConfianca.MEDIO, FonteTipo.MATERIAL_APOIO, Autoridade.DESCONHECIDA)
        assert score == 62.0

    def test_score_base_baixo(self):
        score = calcular_prioridade_recuperacao(PesoConfianca.BAIXO, FonteTipo.MATERIAL_APOIO, Autoridade.DESCONHECIDA)
        assert score == 32.0

    def test_lei_planalto_alta_confianca(self):
        score = calcular_prioridade_recuperacao(PesoConfianca.ALTO, FonteTipo.LEI, Autoridade.PLANALTO)
        assert score == 140.0

    def test_lei_oficial_maior_que_material_anotado(self):
        score_lei = calcular_prioridade_recuperacao(PesoConfianca.ALTO, FonteTipo.LEI, Autoridade.PLANALTO)
        score_material = calcular_prioridade_recuperacao(
            PesoConfianca.ALTO,
            FonteTipo.MATERIAL_APOIO,
            Autoridade.MATERIAL_PROPRIO,
            tem_atencao=True,
            tem_anotacao=True,
            relevancia_estudo="alta",
        )
        assert score_lei > score_material

    def test_atencao_melhora_score(self):
        score_sem = calcular_prioridade_recuperacao(PesoConfianca.MEDIO, FonteTipo.RESOLUCAO, Autoridade.TSE)
        score_com = calcular_prioridade_recuperacao(PesoConfianca.MEDIO, FonteTipo.RESOLUCAO, Autoridade.TSE, tem_atencao=True)
        assert score_com > score_sem
        assert score_com - score_sem == 8.0

    def test_penalizacoes_reduzem_score(self):
        score_normal = calcular_prioridade_recuperacao(PesoConfianca.MEDIO, FonteTipo.DOCTRINA, Autoridade.DESCONHECIDA)
        score_penalizado = calcular_prioridade_recuperacao(
            PesoConfianca.MEDIO,
            FonteTipo.DOCTRINA,
            Autoridade.DESCONHECIDA,
            editorializado=True,
            chunk_pobre=True,
        )
        assert score_penalizado < score_normal
        assert score_normal - score_penalizado == 18.0

    def test_resolucao_tse_maior_que_questao_comentada(self):
        score_resolucao = calcular_prioridade_recuperacao(PesoConfianca.ALTO, FonteTipo.RESOLUCAO, Autoridade.TSE)
        score_questao = calcular_prioridade_recuperacao(
            PesoConfianca.MEDIO,
            FonteTipo.QUESTAO,
            Autoridade.BANCA,
            tem_atencao=True,
        )
        assert score_resolucao > score_questao


class TestScoreConstants:
    def test_peso_confianca_scores(self):
        assert PESO_CONFIANCA_SCORE[PesoConfianca.ALTO] == 100
        assert PESO_CONFIANCA_SCORE[PesoConfianca.MEDIO] == 70
        assert PESO_CONFIANCA_SCORE[PesoConfianca.BAIXO] == 40

    def test_fonte_tipo_lei_positivo(self):
        assert FONTE_TIPO_SCORE[FonteTipo.LEI] > 0

    def test_fonte_tipo_questao_negativo(self):
        assert FONTE_TIPO_SCORE[FonteTipo.QUESTAO] < 0

    def test_autoridade_planalto_alto(self):
        assert AUTORIDADE_SCORE[Autoridade.PLANALTO] == 20

    def test_autoridade_desconhecida_negativo(self):
        assert AUTORIDADE_SCORE[Autoridade.DESCONHECIDA] < 0
