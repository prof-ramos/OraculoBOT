-- Migration: 001_rag_lote1_ingestion_schema.sql
-- Description: Schema de persistencia para o pipeline de ingestao do RAG Lote 1
-- Schema: juridico
-- Baseado em: docs/RAG_LOTE1/PASSO_5_ESPECIFICACAO_IMPLEMENTACAO.md

-- Criar schema juridico se nao existir
CREATE SCHEMA IF NOT EXISTS juridico;

-- ============================================================================
-- ENUMS
-- ============================================================================

-- Status de rodada de ingestao
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_ingestao_run') THEN
        CREATE TYPE juridico.status_ingestao_run AS ENUM (
            'planned', 'running', 'validated', 'failed', 'rolled_back'
        );
    END IF;
END $$;

-- Status de documento
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_documento') THEN
        CREATE TYPE juridico.status_documento AS ENUM (
            'aprovado', 'quarentena', 'descartado', 'revisao_manual'
        );
    END IF;
END $$;

-- Status de extracao
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_extracao') THEN
        CREATE TYPE juridico.status_extracao AS ENUM (
            'ok', 'parcial', 'falha'
        );
    END IF;
END $$;

-- Status de validacao
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_validacao') THEN
        CREATE TYPE juridico.status_validacao AS ENUM (
            'pendente', 'aprovado', 'rejeitado'
        );
    END IF;
END $$;

-- Status de embedding
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_embedding') THEN
        CREATE TYPE juridico.status_embedding AS ENUM (
            'pendente', 'gerado', 'falha'
        );
    END IF;
END $$;

-- Tipo de teste de retrieval
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_teste_retrieval') THEN
        CREATE TYPE juridico.tipo_teste_retrieval AS ENUM (
            'canonica', 'autoridade', 'contaminacao', 'atencao'
        );
    END IF;
END $$;

-- Resultado de teste
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'resultado_teste') THEN
        CREATE TYPE juridico.resultado_teste AS ENUM (
            'pass', 'warning', 'fail'
        );
    END IF;
END $$;

-- Status de revisao de quarentena
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_review') THEN
        CREATE TYPE juridico.status_review AS ENUM (
            'pendente', 'liberado', 'mantido_fora'
        );
    END IF;
END $$;

-- ============================================================================
-- TABELA 1: ingestion_runs
-- Finalidade: Registrar cada rodada de ingestao de forma auditavel
-- ============================================================================

CREATE TABLE IF NOT EXISTS juridico.ingestion_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_key VARCHAR(128) NOT NULL UNIQUE,
    lote VARCHAR(64) NOT NULL,
    bloco_logico VARCHAR(64) NOT NULL,
    pasta_origem TEXT NOT NULL,
    status juridico.status_ingestao_run NOT NULL DEFAULT 'planned',
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_by VARCHAR(128) DEFAULT 'system',
    observacoes TEXT,
    stats_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE juridico.ingestion_runs IS 'Registra cada rodada de ingestao de forma auditavel';
COMMENT ON COLUMN juridico.ingestion_runs.run_key IS 'Chave unica da rodada (ex: lote1_v1_eleitoral)';
COMMENT ON COLUMN juridico.ingestion_runs.lote IS 'Identificador do lote (ex: lote1)';
COMMENT ON COLUMN juridico.ingestion_runs.bloco_logico IS 'Bloco logico processado (ex: eleitoral, administrativo)';
COMMENT ON COLUMN juridico.ingestion_runs.pasta_origem IS 'Caminho da pasta fisica de origem';
COMMENT ON COLUMN juridico.ingestion_runs.status IS 'Status atual da rodada';
COMMENT ON COLUMN juridico.ingestion_runs.stats_json IS 'Estatisticas da rodada em JSON';

-- Indices para ingestion_runs
CREATE INDEX IF NOT EXISTS idx_ingestion_runs_bloco_logico ON juridico.ingestion_runs(bloco_logico);
CREATE INDEX IF NOT EXISTS idx_ingestion_runs_status ON juridico.ingestion_runs(status);
CREATE INDEX IF NOT EXISTS idx_ingestion_runs_lote ON juridico.ingestion_runs(lote);
CREATE INDEX IF NOT EXISTS idx_ingestion_runs_created_at ON juridico.ingestion_runs(created_at DESC);

-- ============================================================================
-- TABELA 2: source_documents
-- Finalidade: Representar o documento fonte antes/depois da extracao/classificacao
-- ============================================================================

CREATE TABLE IF NOT EXISTS juridico.source_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ingestion_run_id UUID NOT NULL REFERENCES juridico.ingestion_runs(id) ON DELETE CASCADE,
    documento_id_externo VARCHAR(256) NOT NULL,
    arquivo_origem TEXT NOT NULL,
    arquivo_nome VARCHAR(512) NOT NULL,
    pasta_origem TEXT NOT NULL,
    bloco_logico VARCHAR(64) NOT NULL,
    hash_sha256 VARCHAR(64) NOT NULL,
    extensao VARCHAR(32) NOT NULL,
    tamanho_bytes BIGINT NOT NULL DEFAULT 0,

    -- Extracao
    texto_extraido TEXT,
    extracao_status juridico.status_extracao NOT NULL DEFAULT 'ok',
    extracao_metodo VARCHAR(128),

    -- Classificacao
    ramo VARCHAR(64) NOT NULL,
    fonte_tipo VARCHAR(64) NOT NULL,
    autoridade VARCHAR(64) NOT NULL DEFAULT 'desconhecida',
    tem_anotacao BOOLEAN NOT NULL DEFAULT FALSE,
    tem_atencao_documento BOOLEAN NOT NULL DEFAULT FALSE,
    peso_confianca VARCHAR(16) NOT NULL DEFAULT 'medio',
    ano INTEGER,
    banca VARCHAR(128),
    subtema VARCHAR(256),
    tipo VARCHAR(128),

    -- Status
    status_documento juridico.status_documento NOT NULL DEFAULT 'aprovado',
    motivo_status TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraint unica por run
    UNIQUE(ingestion_run_id, documento_id_externo)
);

COMMENT ON TABLE juridico.source_documents IS 'Documentos fonte com extracao e classificacao';
COMMENT ON COLUMN juridico.source_documents.documento_id_externo IS 'Identificador unico do documento (hash ou derivado)';
COMMENT ON COLUMN juridico.source_documents.hash_sha256 IS 'Hash SHA-256 do arquivo';
COMMENT ON COLUMN juridico.source_documents.ramo IS 'Ramo juridico (ex: eleitoral, administrativo)';
COMMENT ON COLUMN juridico.source_documents.fonte_tipo IS 'Tipo de fonte (lei, resolucao, doutrina...)';
COMMENT ON COLUMN juridico.source_documents.autoridade IS 'Autoridade emissora (planalto, stf, tse...)';
COMMENT ON COLUMN juridico.source_documents.peso_confianca IS 'Nivel de confianca na classificacao (alto, medio, baixo)';
COMMENT ON COLUMN juridico.source_documents.tem_atencao_documento IS 'Se ao menos um chunk tem marcacao #Atencao';

-- Indices para source_documents
CREATE INDEX IF NOT EXISTS idx_source_documents_run ON juridico.source_documents(ingestion_run_id);
CREATE INDEX IF NOT EXISTS idx_source_documents_bloco_logico ON juridico.source_documents(bloco_logico);
CREATE INDEX IF NOT EXISTS idx_source_documents_ramo ON juridico.source_documents(ramo);
CREATE INDEX IF NOT EXISTS idx_source_documents_fonte_tipo ON juridico.source_documents(fonte_tipo);
CREATE INDEX IF NOT EXISTS idx_source_documents_autoridade ON juridico.source_documents(autoridade);
CREATE INDEX IF NOT EXISTS idx_source_documents_status ON juridico.source_documents(status_documento);
CREATE INDEX IF NOT EXISTS idx_source_documents_hash ON juridico.source_documents(hash_sha256);
CREATE INDEX IF NOT EXISTS idx_source_documents_ano ON juridico.source_documents(ano);
CREATE INDEX IF NOT EXISTS idx_source_documents_atencao ON juridico.source_documents(tem_atencao_documento);

-- ============================================================================
-- TABELA 3: document_chunks
-- Finalidade: Armazenar a unidade real de recuperacao
-- ============================================================================

CREATE TABLE IF NOT EXISTS juridico.document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ingestion_run_id UUID NOT NULL REFERENCES juridico.ingestion_runs(id) ON DELETE CASCADE,
    source_document_id UUID NOT NULL REFERENCES juridico.source_documents(id) ON DELETE CASCADE,
    chunk_id_externo VARCHAR(256) NOT NULL UNIQUE,
    ordem_chunk INTEGER NOT NULL DEFAULT 0,
    texto_chunk TEXT NOT NULL,

    -- Metadados estruturais
    titulo_secao VARCHAR(512),
    artigo_ref VARCHAR(128),

    -- Metadados herdados + especificos
    ramo VARCHAR(64) NOT NULL,
    bloco_logico VARCHAR(64) NOT NULL,
    fonte_tipo VARCHAR(64) NOT NULL,
    autoridade VARCHAR(64) NOT NULL DEFAULT 'desconhecida',
    arquivo_origem TEXT NOT NULL,
    pasta_origem TEXT NOT NULL,

    -- Sinais didaticos
    tem_anotacao BOOLEAN NOT NULL DEFAULT FALSE,
    tem_atencao BOOLEAN NOT NULL DEFAULT FALSE,
    tipo_marcacao VARCHAR(64),
    relevancia_estudo VARCHAR(32),

    -- Classificacao
    peso_confianca VARCHAR(16) NOT NULL DEFAULT 'medio',
    ano INTEGER,
    banca VARCHAR(128),
    subtema VARCHAR(256),
    tipo VARCHAR(128),

    -- Score e validacao
    prioridade_recuperacao NUMERIC(10,2) NOT NULL DEFAULT 0,
    status_validacao juridico.status_validacao NOT NULL DEFAULT 'pendente',

    -- Embedding
    embedding_status juridico.status_embedding NOT NULL DEFAULT 'pendente',
    embedding_model VARCHAR(128),
    embedding_vector VECTOR(1536),  -- OpenAI text-embedding-3-small

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE juridico.document_chunks IS 'Chunks de documentos para recuperacao RAG';
COMMENT ON COLUMN juridico.document_chunks.chunk_id_externo IS 'Identificador unico do chunk';
COMMENT ON COLUMN juridico.document_chunks.ordem_chunk IS 'Ordem do chunk no documento original';
COMMENT ON COLUMN juridico.document_chunks.texto_chunk IS 'Texto do chunk';
COMMENT ON COLUMN juridico.document_chunks.titulo_secao IS 'Titulo da secao se detectado';
COMMENT ON COLUMN juridico.document_chunks.artigo_ref IS 'Referencia de artigo se detectado';
COMMENT ON COLUMN juridico.document_chunks.tem_atencao IS 'Se contem marcacao #Atencao';
COMMENT ON COLUMN juridico.document_chunks.prioridade_recuperacao IS 'Score heuristico de prioridade';
COMMENT ON COLUMN juridico.document_chunks.embedding_vector IS 'Vetor de embedding (OpenAI 1536 dim)';

-- Indices para document_chunks_ingestion
CREATE INDEX IF NOT EXISTS idx_document_chunks_run ON juridico.document_chunks(ingestion_run_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document ON juridico.document_chunks(source_document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_ramo ON juridico.document_chunks(ramo);
CREATE INDEX IF NOT EXISTS idx_document_chunks_bloco_logico ON juridico.document_chunks(bloco_logico);
CREATE INDEX IF NOT EXISTS idx_document_chunks_fonte_tipo ON juridico.document_chunks(fonte_tipo);
CREATE INDEX IF NOT EXISTS idx_document_chunks_autoridade ON juridico.document_chunks(autoridade);
CREATE INDEX IF NOT EXISTS idx_document_chunks_atencao ON juridico.document_chunks(tem_atencao);
CREATE INDEX IF NOT EXISTS idx_document_chunks_peso ON juridico.document_chunks(peso_confianca);
CREATE INDEX IF NOT EXISTS idx_document_chunks_validacao ON juridico.document_chunks(status_validacao);
CREATE INDEX IF NOT EXISTS idx_document_chunks_prioridade ON juridico.document_chunks(prioridade_recuperacao DESC);

-- Indice vetorial para embedding (HNSW para alta performance)
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
    ON juridico.document_chunks
    USING hnsw (embedding_vector vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- ============================================================================
-- TABELA 4: retrieval_eval_runs
-- Finalidade: Guardar testes de recuperacao por rodada
-- ============================================================================

CREATE TABLE IF NOT EXISTS juridico.retrieval_eval_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ingestion_run_id UUID REFERENCES juridico.ingestion_runs(id) ON DELETE SET NULL,
    bloco_logico VARCHAR(64) NOT NULL,
    query TEXT NOT NULL,
    tipo_teste juridico.tipo_teste_retrieval NOT NULL DEFAULT 'canonica',
    top_k_json JSONB,
    resultado juridico.resultado_teste NOT NULL DEFAULT 'warning',
    observacao TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE juridico.retrieval_eval_runs IS 'Testes de recuperacao por rodada de ingestao';
COMMENT ON COLUMN juridico.retrieval_eval_runs.tipo_teste IS 'Tipo de teste: canonica, autoridade, contaminacao, atencao';
COMMENT ON COLUMN juridico.retrieval_eval_runs.top_k_json IS 'Top-k resultados em JSON';
COMMENT ON COLUMN juridico.retrieval_eval_runs.resultado IS 'Resultado: pass, warning, fail';

-- Indices para retrieval_eval_runs
CREATE INDEX IF NOT EXISTS idx_eval_runs_ingestion ON juridico.retrieval_eval_runs(ingestion_run_id);
CREATE INDEX IF NOT EXISTS idx_eval_runs_bloco ON juridico.retrieval_eval_runs(bloco_logico);
CREATE INDEX IF NOT EXISTS idx_eval_runs_resultado ON juridico.retrieval_eval_runs(resultado);
CREATE INDEX IF NOT EXISTS idx_eval_runs_tipo ON juridico.retrieval_eval_runs(tipo_teste);

-- ============================================================================
-- TABELA 5: document_quarantine
-- Finalidade: Segurar documentos problematicos fora do fluxo principal
-- ============================================================================

CREATE TABLE IF NOT EXISTS juridico.document_quarantine (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_document_id UUID NOT NULL REFERENCES juridico.source_documents(id) ON DELETE CASCADE,
    motivo VARCHAR(256) NOT NULL,
    detalhes TEXT,
    needs_review BOOLEAN NOT NULL DEFAULT TRUE,
    review_status juridico.status_review NOT NULL DEFAULT 'pendente',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMPTZ
);

COMMENT ON TABLE juridico.document_quarantine IS 'Documentos retidos para revisao fora do fluxo principal';
COMMENT ON COLUMN juridico.document_quarantine.motivo IS 'Motivo da quarentena (extracao_ruim, classificacao_ambigua, etc)';
COMMENT ON COLUMN juridico.document_quarantine.needs_review IS 'Se precisa revisao manual';
COMMENT ON COLUMN juridico.document_quarantine.review_status IS 'Status da revisao';

-- Indices para document_quarantine
CREATE INDEX IF NOT EXISTS idx_quarantine_document ON juridico.document_quarantine(source_document_id);
CREATE INDEX IF NOT EXISTS idx_quarantine_review ON juridico.document_quarantine(review_status);
CREATE INDEX IF NOT EXISTS idx_quarantine_needs ON juridico.document_quarantine(needs_review) WHERE needs_review = TRUE;

-- ============================================================================
-- TRIGGER PARA updated_at
-- ============================================================================

-- Funcao generica para atualizar updated_at
CREATE OR REPLACE FUNCTION juridico.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para updated_at
DROP TRIGGER IF EXISTS update_source_documents_updated_at ON juridico.source_documents;
CREATE TRIGGER update_source_documents_updated_at
    BEFORE UPDATE ON juridico.source_documents
    FOR EACH ROW
    EXECUTE FUNCTION juridico.update_updated_at_column();

DROP TRIGGER IF EXISTS update_document_chunks_updated_at ON juridico.document_chunks;
CREATE TRIGGER update_document_chunks_updated_at
    BEFORE UPDATE ON juridico.document_chunks
    FOR EACH ROW
    EXECUTE FUNCTION juridico.update_updated_at_column();

-- ============================================================================
-- ROLLBACK (para referencia)
-- ============================================================================
-- Para reverter esta migration:
--
-- DROP TABLE IF EXISTS juridico.document_quarantine CASCADE;
-- DROP TABLE IF EXISTS juridico.retrieval_eval_runs CASCADE;
-- DROP TABLE IF EXISTS juridico.document_chunks CASCADE;
-- DROP TABLE IF EXISTS juridico.source_documents CASCADE;
-- DROP TABLE IF EXISTS juridico.ingestion_runs CASCADE;
-- DROP FUNCTION IF EXISTS juridico.update_updated_at_column() CASCADE;
-- DROP TYPE IF EXISTS juridico.status_review CASCADE;
-- DROP TYPE IF EXISTS juridico.resultado_teste CASCADE;
-- DROP TYPE IF EXISTS juridico.tipo_teste_retrieval CASCADE;
-- DROP TYPE IF EXISTS juridico.status_embedding CASCADE;
-- DROP TYPE IF EXISTS juridico.status_validacao CASCADE;
-- DROP TYPE IF EXISTS juridico.status_extracao CASCADE;
-- DROP TYPE IF EXISTS juridico.status_documento CASCADE;
-- DROP TYPE IF EXISTS juridico.status_ingestao_run CASCADE;
