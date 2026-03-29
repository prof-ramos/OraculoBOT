"""Modelos e enums para o pipeline de ingestao RAG Lote 1.

Especificacao baseada em docs/RAG_LOTE1/PASSO_5_ESPECIFICACAO_IMPLEMENTACAO.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4


# ─────────────────────────────────────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────────────────────────────────────


class RamoJuridico(str, Enum):
    """Ramos juridicos do Lote 1."""
    ADMINISTRATIVO = "administrativo"
    CONSTITUCIONAL = "constitucional"
    DIREITOS_HUMANOS = "direitos_humanos"
    INTERNACIONAL = "internacional"
    PENAL = "penal"
    ELEITORAL = "eleitoral"
    ECA = "eca"
    EDUCACAO = "educacao"
    CONSUMIDOR = "consumidor"


class FonteTipo(str, Enum):
    """Tipos de fonte documental."""
    LEI = "lei"
    LEGISLACAO_ANOTADA = "legislacao_anotada"
    RESOLUCAO = "resolucao"
    DECRETO = "decreto"
    DOUTRINA = "doutrina"
    DOCTRINA = "doutrina"  # compat alias
    QUESTAO = "questao"
    MATERIAL_APOIO = "material_de_apoio"
    CONVENCAO = "convencao"
    SUMULA = "sumula"


class Autoridade(str, Enum):
    """Autoridades emissorass de documentos juridicos."""
    PLANALTO = "planalto"
    STF = "stf"
    STJ = "stj"
    TSE = "tse"
    TCU = "tcu"
    CONANDA = "conanda"
    CNJ = "cnj"
    CNMP = "cnmp"
    ONU = "onu"
    OEA = "oea"
    OIT = "oit"
    BANCA = "banca"
    MATERIAL_PROPRIO = "material_proprio"
    DESCONHECIDA = "desconhecida"


class PesoConfianca(str, Enum):
    """Nivel de confianca na classificacao do documento."""
    ALTO = "alto"
    MEDIO = "medio"
    BAIXO = "baixo"


class StatusDocumento(str, Enum):
    """Status de processamento do documento."""
    APROVADO = "aprovado"
    QUARENTENA = "quarentena"
    DESCARTADO = "descartado"
    REVISAO_MANUAL = "revisao_manual"


class StatusIngestaoRun(str, Enum):
    """Status de uma rodada de ingestao."""
    PLANNED = "planned"
    RUNNING = "running"
    VALIDATED = "validated"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class StatusExtracao(str, Enum):
    """Status de extracao de texto."""
    OK = "ok"
    PARCIAL = "parcial"
    FALHA = "falha"


class StatusValidacao(str, Enum):
    """Status de validacao de chunk."""
    PENDENTE = "pendente"
    APROVADO = "aprovado"
    REJEITADO = "rejeitado"


class StatusEmbedding(str, Enum):
    """Status de geracao de embedding."""
    PENDENTE = "pendente"
    GERADO = "gerado"
    FALHA = "falha"


class TipoTesteRetrieval(str, Enum):
    """Tipos de teste de recuperacao."""
    CANONICA = "canonica"
    AUTORIDADE = "autoridade"
    CONTAMINACAO = "contaminacao"
    ATENCAO = "atencao"


class ResultadoTeste(str, Enum):
    """Resultado de um teste de recuperacao."""
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


class StatusReview(str, Enum):
    """Status de revisao de documento em quarentena."""
    PENDENTE = "pendente"
    LIBERADO = "liberado"
    MANTIDO_FORA = "mantido_fora"


# ─────────────────────────────────────────────────────────────────────────────
# MODELOS
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class IngestionRun:
    """Rodada de ingestao auditavel.

    Mapeia para a tabela 'ingestion_runs' no schema juridico.
    """
    id: UUID = field(default_factory=uuid4)
    run_key: str = ""  # ex: lote1_v1_eleitoral
    lote: str = "lote1"
    bloco_logico: str = ""  # ex: eleitoral
    pasta_origem: str = ""
    status: StatusIngestaoRun = StatusIngestaoRun.PLANNED
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_by: str = ""
    observacoes: Optional[str] = None
    stats_json: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Garante tipos corretos apos inicializacao."""
        if isinstance(self.status, str):
            self.status = StatusIngestaoRun(self.status)


@dataclass
class SourceDocument:
    """Documento fonte antes/depois da extracao e classificacao.

    Mapeia para a tabela 'source_documents' no schema juridico.
    """
    id: UUID = field(default_factory=uuid4)
    ingestion_run_id: Optional[UUID] = None
    documento_id_externo: str = ""  # hash ou identificador unico
    arquivo_origem: str = ""
    arquivo_nome: str = ""
    pasta_origem: str = ""
    bloco_logico: str = ""
    hash_sha256: str = ""
    extensao: str = ""
    tamanho_bytes: int = 0

    # Extracao
    texto_extraido: Optional[str] = None
    extracao_status: StatusExtracao = StatusExtracao.OK
    extracao_metodo: Optional[str] = None

    # Classificacao
    ramo: RamoJuridico = RamoJuridico.ELEITORAL
    fonte_tipo: FonteTipo = FonteTipo.MATERIAL_APOIO
    autoridade: Autoridade = Autoridade.DESCONHECIDA
    tem_anotacao: bool = False
    tem_atencao_documento: bool = False
    peso_confianca: PesoConfianca = PesoConfianca.MEDIO
    ano: Optional[int] = None
    banca: Optional[str] = None
    subtema: Optional[str] = None
    tipo: Optional[str] = None

    # Status
    status_documento: StatusDocumento = StatusDocumento.APROVADO
    motivo_status: Optional[str] = None

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Garante tipos corretos apos inicializacao."""
        if isinstance(self.ramo, str):
            self.ramo = RamoJuridico(self.ramo)
        if isinstance(self.fonte_tipo, str):
            self.fonte_tipo = FonteTipo(self.fonte_tipo)
        if isinstance(self.autoridade, str):
            self.autoridade = Autoridade(self.autoridade)
        if isinstance(self.peso_confianca, str):
            self.peso_confianca = PesoConfianca(self.peso_confianca)
        if isinstance(self.extracao_status, str):
            self.extracao_status = StatusExtracao(self.extracao_status)
        if isinstance(self.status_documento, str):
            self.status_documento = StatusDocumento(self.status_documento)


@dataclass
class DocumentChunk:
    """Unidade real de recuperacao.

    Mapeia para a tabela 'document_chunks' no schema juridico.
    """
    id: UUID = field(default_factory=uuid4)
    ingestion_run_id: Optional[UUID] = None
    source_document_id: Optional[UUID] = None
    chunk_id_externo: str = ""
    ordem_chunk: int = 0
    texto_chunk: str = ""

    # Metadados estruturais
    titulo_secao: Optional[str] = None
    artigo_ref: Optional[str] = None

    # Metadados herdados + especificos
    ramo: RamoJuridico = RamoJuridico.ELEITORAL
    bloco_logico: str = ""
    fonte_tipo: FonteTipo = FonteTipo.MATERIAL_APOIO
    autoridade: Autoridade = Autoridade.DESCONHECIDA
    arquivo_origem: str = ""
    pasta_origem: str = ""

    # Sinais didaticos
    tem_anotacao: bool = False
    tem_atencao: bool = False
    tipo_marcacao: Optional[str] = None
    relevancia_estudo: Optional[str] = None

    # Classificacao
    peso_confianca: PesoConfianca = PesoConfianca.MEDIO
    ano: Optional[int] = None
    banca: Optional[str] = None
    subtema: Optional[str] = None
    tipo: Optional[str] = None

    # Score e validacao
    prioridade_recuperacao: float = 0.0
    status_validacao: StatusValidacao = StatusValidacao.PENDENTE

    # Embedding
    embedding_status: StatusEmbedding = StatusEmbedding.PENDENTE
    embedding_model: Optional[str] = None
    embedding_vector: Optional[List[float]] = None

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Garante tipos corretos apos inicializacao."""
        if isinstance(self.ramo, str):
            self.ramo = RamoJuridico(self.ramo)
        if isinstance(self.fonte_tipo, str):
            self.fonte_tipo = FonteTipo(self.fonte_tipo)
        if isinstance(self.autoridade, str):
            self.autoridade = Autoridade(self.autoridade)
        if isinstance(self.peso_confianca, str):
            self.peso_confianca = PesoConfianca(self.peso_confianca)
        if isinstance(self.status_validacao, str):
            self.status_validacao = StatusValidacao(self.status_validacao)
        if isinstance(self.embedding_status, str):
            self.embedding_status = StatusEmbedding(self.embedding_status)


@dataclass
class RetrievalEvalRun:
    """Resultado de teste de recuperacao por rodada.

    Mapeia para a tabela 'retrieval_eval_runs' no schema juridico.
    """
    id: UUID = field(default_factory=uuid4)
    ingestion_run_id: Optional[UUID] = None
    bloco_logico: str = ""
    query: str = ""
    tipo_teste: TipoTesteRetrieval = TipoTesteRetrieval.CANONICA
    top_k_json: Optional[Dict[str, Any]] = None
    resultado: ResultadoTeste = ResultadoTeste.WARNING
    observacao: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Garante tipos corretos apos inicializacao."""
        if isinstance(self.tipo_teste, str):
            self.tipo_teste = TipoTesteRetrieval(self.tipo_teste)
        if isinstance(self.resultado, str):
            self.resultado = ResultadoTeste(self.resultado)


@dataclass
class DocumentQuarantine:
    """Documento retido para revisao fora do fluxo principal.

    Mapeia para a tabela 'document_quarantine' no schema juridico.
    """
    id: UUID = field(default_factory=uuid4)
    source_document_id: Optional[UUID] = None
    motivo: str = ""
    detalhes: Optional[str] = None
    needs_review: bool = True
    review_status: StatusReview = StatusReview.PENDENTE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reviewed_at: Optional[datetime] = None

    def __post_init__(self):
        """Garante tipos corretos apos inicializacao."""
        if isinstance(self.review_status, str):
            self.review_status = StatusReview(self.review_status)


# ─────────────────────────────────────────────────────────────────────────────
# SCORE HEURISTICO
# ─────────────────────────────────────────────────────────────────────────────

# Pesos base por confianca
PESO_CONFIANCA_SCORE = {
    PesoConfianca.ALTO: 100,
    PesoConfianca.MEDIO: 70,
    PesoConfianca.BAIXO: 40,
}

# Ajustes por tipo de fonte
FONTE_TIPO_SCORE = {
    FonteTipo.LEI: 20,
    FonteTipo.RESOLUCAO: 18,
    FonteTipo.DECRETO: 15,
    FonteTipo.CONVENCAO: 15,
    FonteTipo.SUMULA: 18,
    FonteTipo.LEGISLACAO_ANOTADA: 8,
    FonteTipo.DOUTRINA: 5,
    FonteTipo.MATERIAL_APOIO: 2,
    FonteTipo.QUESTAO: -5,
}

# Ajustes por autoridade
AUTORIDADE_SCORE = {
    Autoridade.PLANALTO: 20,
    Autoridade.STF: 20,
    Autoridade.STJ: 18,
    Autoridade.TSE: 18,
    Autoridade.TCU: 12,
    Autoridade.CNJ: 10,
    Autoridade.CNMP: 10,
    Autoridade.CONANDA: 10,
    Autoridade.ONU: 12,
    Autoridade.OEA: 12,
    Autoridade.OIT: 10,
    Autoridade.BANCA: -5,
    Autoridade.MATERIAL_PROPRIO: -2,
    Autoridade.DESCONHECIDA: -10,
}

# Ajustes por sinais didaticos
SINAL_DIDATICO_SCORE = {
    "tem_atencao": 8,
    "relevancia_alta": 5,
    "tem_anotacao": 2,
    "editorializado": -10,
    "origem_pouco_clara": -15,
    "chunk_pobre": -8,
}


def calcular_prioridade_recuperacao(
    peso_confianca: PesoConfianca,
    fonte_tipo: FonteTipo,
    autoridade: Autoridade,
    tem_atencao: bool = False,
    tem_anotacao: bool = False,
    relevancia_estudo: Optional[str] = None,
    editorializado: bool = False,
    origem_pouco_clara: bool = False,
    chunk_pobre: bool = False,
) -> float:
    """Calcula score heuristico de prioridade de recuperacao.

    Args:
        peso_confianca: Nivel de confianca na classificacao.
        fonte_tipo: Tipo de fonte documental.
        autoridade: Autoridade emissora.
        tem_atencao: Se tem marcacao #Atencao.
        tem_anotacao: Se tem anotacoes/comentarios.
        relevancia_estudo: Nivel de relevancia (alta/media/baixa).
        editorializado: Se material excessivamente editorializado.
        origem_pouco_clara: Se origem nao esta clara.
        chunk_pobre: Se chunk muito curto ou pobre.

    Returns:
        Score de prioridade (maior = mais prioritario).
    """
    score = PESO_CONFIANCA_SCORE.get(peso_confianca, 70)

    score += FONTE_TIPO_SCORE.get(fonte_tipo, 0)
    score += AUTORIDADE_SCORE.get(autoridade, 0)

    if tem_atencao:
        score += SINAL_DIDATICO_SCORE["tem_atencao"]
    if tem_anotacao:
        score += SINAL_DIDATICO_SCORE["tem_anotacao"]
    if relevancia_estudo and relevancia_estudo.lower() == "alta":
        score += SINAL_DIDATICO_SCORE["relevancia_alta"]
    if editorializado:
        score += SINAL_DIDATICO_SCORE["editorializado"]
    if origem_pouco_clara:
        score += SINAL_DIDATICO_SCORE["origem_pouco_clara"]
    if chunk_pobre:
        score += SINAL_DIDATICO_SCORE["chunk_pobre"]

    return float(score)
