"""Scanner de arquivos do Lote 1 para o pipeline de ingestao RAG.

Implementa descoberta de arquivos preservando caminho original,
calculando hash SHA-256 e detectando duplicatas.

Especificacao: docs/RAG_LOTE1/IMPLEMENTATION_TODO.md (EPIC 2, Tarefas 2.1-2.3)
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set


# Extensoes suportadas pelo pipeline
EXTENSOES_SUPORTADAS = {
    # Documentos
    ".pdf",
    ".docx",
    ".doc",
    ".txt",
    ".md",
    # Texto estruturado
    ".rtf",
    ".odt",
}

# Pastas a ignorar durante escaneamento
PASTAS_IGNORADAS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
}


@dataclass
class ArquivoDescoberto:
    """Representa um arquivo descoberto pelo scanner.

    Campos conforme especificacao do manifesto.
    """
    caminho_absoluto: str
    caminho_relativo: str  # relativo a raiz do corpus
    arquivo_nome: str
    extensao: str
    tamanho_bytes: int
    hash_sha256: str
    pasta_origem: str
    bloco_logico: str = ""
    eh_duplicata: bool = False
    duplicata_de: Optional[str] = None  # hash do arquivo original
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ResultadoScanner:
    """Resultado completo de uma execucao do scanner."""
    run_key: str
    raiz_corpus: str
    blocos_logicos: List[str]
    arquivos: List[ArquivoDescoberto] = field(default_factory=list)
    duplicatas: Dict[str, List[str]] = field(default_factory=dict)  # hash -> [caminhos]
    total_arquivos: int = 0
    total_duplicatas: int = 0
    erros: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    stats: Dict = field(default_factory=dict)


class ScannerLote1:
    """Scanner de arquivos do Lote 1.

    Percorre pastas fisicas preservando caminho original,
    calcula hash SHA-256, detecta duplicatas e classifica
    blocos logicos.
    """

    def __init__(
        self,
        raiz_corpus: str,
        extensoes: Optional[Set[str]] = None,
        pastas_ignoradas: Optional[Set[str]] = None,
    ):
        """Inicializa o scanner.

        Args:
            raiz_corpus: Caminho raiz do corpus (ex: /data/Lote1)
            extensoes: Conjunto de extensoes a escanear (default: EXTENSOES_SUPORTADAS)
            pastas_ignoradas: Conjunto de nomes de pastas a ignorar
        """
        self.raiz_corpus = Path(raiz_corpus).resolve()
        self.extensoes = extensoes or EXTENSOES_SUPORTADAS
        self.pastas_ignoradas = pastas_ignoradas or PASTAS_IGNORADAS

    def calcular_hash_sha256(self, caminho: Path) -> str:
        """Calcula hash SHA-256 de um arquivo.

        Usa leitura em chunks para arquivos grandes.

        Args:
            caminho: Caminho do arquivo

        Returns:
            Hash SHA-256 em hexadecimal
        """
        sha256_hash = hashlib.sha256()
        with open(caminho, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def inferir_bloco_logico(self, pasta_origem: str) -> str:
        """Infere o bloco logico a partir da pasta de origem.

        Mapeia pastas fisicas para blocos logicos conforme
        PASSO_3_ESTRATEGIA_INGESTAO.md.

        Args:
            pasta_origem: Caminho da pasta de origem

        Returns:
            Bloco logico inferido
        """
        # Mapeamento de pastas fisicas para blocos logicos
        mapeamento_pastas = {
            "eleitoral": "eleitoral",
            "administrativo": "administrativo",
            "penal": "penal",
            "consumidor": "consumidor",
            "eca_e_educacao": "eca",  # Default, sera refinado na classificacao
            "constitucional_direitos_humanos_internacional": "constitucional",  # Default
        }

        # Extrair nome da pasta raiz do bloco
        partes = Path(pasta_origem).parts
        if len(partes) > 0:
            # Tentar encontrar pasta raiz conhecida
            for parte in reversed(partes):
                parte_lower = parte.lower()
                for nome_pasta, bloco in mapeamento_pastas.items():
                    if nome_pasta in parte_lower:
                        return bloco

        return "desconhecido"

    def escanear(
        self,
        pastas_alvo: Optional[List[str]] = None,
        run_key: Optional[str] = None,
    ) -> ResultadoScanner:
        """Escanear arquivos do Lote 1.

        Args:
            pastas_alvo: Lista de pastas a escanear (relativas a raiz).
                        Se None, escaneia todas as pastas.
            run_key: Chave identificadora da rodada.

        Returns:
            ResultadoScanner com todos os arquivos descobertos.
        """
        started_at = datetime.now(timezone.utc)
        run_key = run_key or f"scan_{started_at.strftime('%Y%m%d_%H%M%S')}"

        # Determinar pastas a escanear
        if pastas_alvo:
            pastas = [self.raiz_corpus / p for p in pastas_alvo]
        else:
            pastas = [self.raiz_corpus]

        arquivos: List[ArquivoDescoberto] = []
        hash_para_caminhos: Dict[str, List[str]] = {}
        erros: List[str] = []
        blocos_logicos: Set[str] = set()

        for pasta_base in pastas:
            if not pasta_base.exists():
                erros.append(f"Pasta nao existe: {pasta_base}")
                continue

            for raiz, dirs, files in os.walk(pasta_base):
                # Filtrar pastas ignoradas
                dirs[:] = [d for d in dirs if d not in self.pastas_ignoradas]

                for nome_arquivo in files:
                    caminho = Path(raiz) / nome_arquivo

                    # Verificar extensao
                    extensao = caminho.suffix.lower()
                    if extensao not in self.extensoes:
                        continue

                    try:
                        # Calcular propriedades do arquivo
                        stat = caminho.stat()
                        hash_sha256 = self.calcular_hash_sha256(caminho)
                        caminho_relativo = str(caminho.relative_to(self.raiz_corpus))
                        pasta_origem = str(caminho.parent)

                        # Inferir bloco logico
                        bloco_logico = self.inferir_bloco_logico(pasta_origem)
                        blocos_logicos.add(bloco_logico)

                        # Registrar hash para deteccao de duplicatas
                        if hash_sha256 not in hash_para_caminhos:
                            hash_para_caminhos[hash_sha256] = []

                        hash_para_caminhos[hash_sha256].append(str(caminho))

                        # Criar registro do arquivo
                        arquivo = ArquivoDescoberto(
                            caminho_absoluto=str(caminho),
                            caminho_relativo=caminho_relativo,
                            arquivo_nome=nome_arquivo,
                            extensao=extensao,
                            tamanho_bytes=stat.st_size,
                            hash_sha256=hash_sha256,
                            pasta_origem=pasta_origem,
                            bloco_logico=bloco_logico,
                        )

                        arquivos.append(arquivo)

                    except Exception as e:
                        erros.append(f"Erro ao processar {caminho}: {e}")

        # Marcar duplicatas
        duplicatas: Dict[str, List[str]] = {}
        for hash_val, caminhos in hash_para_caminhos.items():
            if len(caminhos) > 1:
                # Primeiro arquivo e o original, resto sao duplicatas
                original = caminhos[0]
                duplicatas[hash_val] = caminhos

                for arquivo in arquivos:
                    if arquivo.hash_sha256 == hash_val and arquivo.caminho_absoluto != original:
                        arquivo.eh_duplicata = True
                        arquivo.duplicata_de = hash_val

        finished_at = datetime.now(timezone.utc)

        # Calcular estatisticas
        total_duplicatas = sum(len(c) - 1 for c in duplicatas.values())
        stats = {
            "total_arquivos": len(arquivos),
            "total_unicos": len(arquivos) - total_duplicatas,
            "total_duplicatas": total_duplicatas,
            "total_hashes_unicos": len(hash_para_caminhos),
            "extensoes_encontradas": list(set(a.extensao for a in arquivos)),
            "blocos_logicos": list(blocos_logicos),
            "duracao_segundos": (finished_at - started_at).total_seconds(),
        }

        return ResultadoScanner(
            run_key=run_key,
            raiz_corpus=str(self.raiz_corpus),
            blocos_logicos=list(blocos_logicos),
            arquivos=arquivos,
            duplicatas=duplicatas,
            total_arquivos=len(arquivos),
            total_duplicatas=total_duplicatas,
            erros=erros,
            started_at=started_at,
            finished_at=finished_at,
            stats=stats,
        )
