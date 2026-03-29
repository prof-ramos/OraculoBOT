from __future__ import annotations

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
    "Autoridade",
    "calcular_prioridade_recuperacao",
    "DocumentChunk",
    "DocumentQuarantine",
    "FonteTipo",
    "IngestionRepository",
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
]
