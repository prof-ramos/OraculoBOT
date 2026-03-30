from __future__ import annotations

"""Pipeline de ingestao RAG Lote 1."""

from oraculo_bot.ingestion.models import (
    Autoridade,
    DocumentChunk,
    DocumentQuarantine,
    FonteTipo,
    IngestionRun,
    PesoConfianca,
    RamoJuridico,
    RetrievalEvalRun,
    ResultadoTeste,
    SourceDocument,
    StatusDocumento,
    StatusEmbedding,
    StatusExtracao,
    StatusIngestaoRun,
    StatusReview,
    StatusValidacao,
    TipoTesteRetrieval,
    calcular_prioridade_recuperacao,
)
from oraculo_bot.ingestion.repository import IngestionRepository
from oraculo_bot.ingestion.scanner import (
    ScannerLote1,
    ArquivoDescoberto,
    ResultadoScanner,
    EXTENSOES_SUPORTADAS,
)
from oraculo_bot.ingestion.manifest import (
    ManifestoWriter,
    ManifestoReader,
)
from oraculo_bot.ingestion.extractor import (
    ExtratorTexto,
    ResultadoExtracao,
    MetodoExtracao,
    StatusExtracaoTexto,
    TextoRuimDetector,
)

__all__ = [
    # Models
    "Autoridade",
    "DocumentChunk",
    "DocumentQuarantine",
    "FonteTipo",
    "IngestionRun",
    "PesoConfianca",
    "RamoJuridico",
    "RetrievalEvalRun",
    "ResultadoTeste",
    "SourceDocument",
    "StatusDocumento",
    "StatusEmbedding",
    "StatusExtracao",
    "StatusIngestaoRun",
    "StatusReview",
    "StatusValidacao",
    "TipoTesteRetrieval",
    "calcular_prioridade_recuperacao",
    # Repository
    "IngestionRepository",
    # Scanner
    "ScannerLote1",
    "ArquivoDescoberto",
    "ResultadoScanner",
    "EXTENSOES_SUPORTADAS",
    # Manifest
    "ManifestoWriter",
    "ManifestoReader",
    # Extractor
    "ExtratorTexto",
    "ResultadoExtracao",
    "MetodoExtracao",
    "StatusExtracaoTexto",
    "TextoRuimDetector",
]
