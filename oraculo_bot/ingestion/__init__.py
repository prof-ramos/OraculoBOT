"""Pipeline de ingestao RAG Lote 1."""

from oraculo_bot.ingestion.models import (
    # Enums
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
    # Models
    IngestionRun,
    SourceDocument,
    DocumentChunk,
    RetrievalEvalRun,
    DocumentQuarantine,
    # Score
    calcular_prioridade_recuperacao,
)
from oraculo_bot.ingestion.repository import IngestionRepository

__all__ = [
    # Enums
    "RamoJuridico",
    "FonteTipo",
    "Autoridade",
    "PesoConfianca",
    "StatusDocumento",
    "StatusIngestaoRun",
    "StatusExtracao",
    "StatusValidacao",
    "StatusEmbedding",
    "TipoTesteRetrieval",
    "ResultadoTeste",
    "StatusReview",
    # Models
    "IngestionRun",
    "SourceDocument",
    "DocumentChunk",
    "RetrievalEvalRun",
    "DocumentQuarantine",
    # Repository
    "IngestionRepository",
    # Score
    "calcular_prioridade_recuperacao",
]
