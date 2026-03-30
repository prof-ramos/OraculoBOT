"""Manifesto versionado para o pipeline de ingestao RAG Lote 1.

Gera artefatos auditaveis (CSV ou JSONL) que permitem reproduzir
rodadas de ingestao e rastrear arquivos processados.

Especificacao: docs/RAG_LOTE1/IMPLEMENTATION_TODO.md (EPIC 2, Tarefa 2.2)
"""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Optional

from oraculo_bot.ingestion.scanner import ResultadoScanner, ArquivoDescoberto


class ManifestoWriter:
    """Gerador de manifestos versionados para ingestao.

    Suporta dois formatos:
    - CSV: mais legivel para humanos, editavel em planilhas
    - JSONL: mais adequado para processamento programatico
    """

    def __init__(self, diretorio_saida: str) -> None:
        """Inicializa o writer de manifestos.

        Args:
            diretorio_saida: Diretorio onde os manifestos serao salvos
        """
        self.diretorio_saida = Path(diretorio_saida)
        self.diretorio_saida.mkdir(parents=True, exist_ok=True)

    def _nome_arquivo(self, run_key: str, formato: str) -> Path:
        """Gera nome do arquivo de manifesto.

        Args:
            run_key: Chave da rodada
            formato: Formato do arquivo (csv ou jsonl)

        Returns:
            Caminho completo do arquivo
        """
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        return self.diretorio_saida / f"manifest_{run_key}_{timestamp}.{formato}"

    def _arquivo_para_dict(self, arquivo: ArquivoDescoberto) -> dict:
        """Converte ArquivoDescoberto para dicionario serializavel.

        Args:
            arquivo: Arquivo descoberto

        Returns:
            Dicionario com campos do arquivo
        """
        return {
            "caminho_absoluto": arquivo.caminho_absoluto,
            "caminho_relativo": arquivo.caminho_relativo,
            "arquivo_nome": arquivo.arquivo_nome,
            "extensao": arquivo.extensao,
            "tamanho_bytes": arquivo.tamanho_bytes,
            "hash_sha256": arquivo.hash_sha256,
            "pasta_origem": arquivo.pasta_origem,
            "bloco_logico": arquivo.bloco_logico,
            "eh_duplicata": arquivo.eh_duplicata,
            "duplicata_de": arquivo.duplicata_de or "",
        }

    def escrever_csv(
        self,
        resultado: ResultadoScanner,
        arquivo_saida: Optional[str] = None,
    ) -> Path:
        """Escreve manifesto em formato CSV.

        Args:
            resultado: Resultado do scanner
            arquivo_saida: Caminho do arquivo de saida (opcional)

        Returns:
            Caminho do arquivo gerado
        """
        if arquivo_saida:
            caminho = Path(arquivo_saida)
        else:
            caminho = self._nome_arquivo(resultado.run_key, "csv")

        campos = [
            "caminho_absoluto",
            "caminho_relativo",
            "arquivo_nome",
            "extensao",
            "tamanho_bytes",
            "hash_sha256",
            "pasta_origem",
            "bloco_logico",
            "eh_duplicata",
            "duplicata_de",
        ]

        with open(caminho, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=campos)
            writer.writeheader()

            for arquivo in resultado.arquivos:
                writer.writerow(self._arquivo_para_dict(arquivo))

        return caminho

    def escrever_jsonl(
        self,
        resultado: ResultadoScanner,
        arquivo_saida: Optional[str] = None,
        *,
        incluir_metadados: bool = True,
    ) -> Path:
        """Escreve manifesto em formato JSONL.

        JSONL (JSON Lines) e adequado para processamento streaming
        e integracao com pipelines de dados.

        Args:
            resultado: Resultado do scanner
            arquivo_saida: Caminho do arquivo de saida (opcional)
            incluir_metadados: Se deve incluir metadados da rodada

        Returns:
            Caminho do arquivo gerado
        """
        if arquivo_saida:
            caminho = Path(arquivo_saida)
        else:
            caminho = self._nome_arquivo(resultado.run_key, "jsonl")

        with open(caminho, "w", encoding="utf-8") as f:
            # Primeira linha: metadados da rodada
            if incluir_metadados:
                metadados = {
                    "_meta": True,
                    "run_key": resultado.run_key,
                    "raiz_corpus": resultado.raiz_corpus,
                    "blocos_logicos": resultado.blocos_logicos,
                    "total_arquivos": resultado.total_arquivos,
                    "total_duplicatas": resultado.total_duplicatas,
                    "started_at": resultado.started_at.isoformat() if resultado.started_at else None,
                    "finished_at": resultado.finished_at.isoformat() if resultado.finished_at else None,
                    "stats": resultado.stats,
                    "erros": resultado.erros,
                }
                f.write(json.dumps(metadados, ensure_ascii=False) + "\n")

            # Linhas subsequentes: arquivos
            for arquivo in resultado.arquivos:
                registro = self._arquivo_para_dict(arquivo)
                registro["_run_key"] = resultado.run_key
                f.write(json.dumps(registro, ensure_ascii=False) + "\n")

        return caminho

    def escrever_resumo(
        self,
        resultado: ResultadoScanner,
        arquivo_saida: Optional[str] = None,
    ) -> Path:
        """Escreve resumo da rodada em formato JSON.

        Args:
            resultado: Resultado do scanner
            arquivo_saida: Caminho do arquivo de saida (opcional)

        Returns:
            Caminho do arquivo gerado
        """
        if arquivo_saida:
            caminho = Path(arquivo_saida)
        else:
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            caminho = self.diretorio_saida / f"summary_{resultado.run_key}_{timestamp}.json"

        resumo = {
            "run_key": resultado.run_key,
            "raiz_corpus": resultado.raiz_corpus,
            "blocos_logicos": resultado.blocos_logicos,
            "stats": resultado.stats,
            "duplicatas_resumo": {
                hash_val: len(caminhos)
                for hash_val, caminhos in resultado.duplicatas.items()
            },
            "erros": resultado.erros,
            "started_at": resultado.started_at.isoformat() if resultado.started_at else None,
            "finished_at": resultado.finished_at.isoformat() if resultado.finished_at else None,
        }

        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(resumo, f, ensure_ascii=False, indent=2)

        return caminho


class ManifestoReader:
    """Leitor de manifestos para reprocessamento.

    Permite carregar manifestos existentes para:
    - Comparar rodadas
    - Reprocessar arquivos especificos
    - Validar integridade
    """

    @staticmethod
    def ler_jsonl(caminho: str) -> tuple[dict, list[dict]]:
        """Le manifesto em formato JSONL.

        Args:
            caminho: Caminho do arquivo

        Returns:
            Tupla (metadados, lista_de_arquivos)
        """
        metadados = {}
        arquivos = []

        with open(caminho, "r", encoding="utf-8") as f:
            for linha in f:
                registro = json.loads(linha.strip())

                if registro.get("_meta"):
                    metadados = registro
                else:
                    arquivos.append(registro)

        return metadados, arquivos

    @staticmethod
    def ler_csv(caminho: str) -> list[dict]:
        """Le manifesto em formato CSV.

        Args:
            caminho: Caminho do arquivo

        Returns:
            Lista de dicionarios com dados dos arquivos
        """
        arquivos = []

        with open(caminho, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for linha in reader:
                # Converter tipos
                linha["tamanho_bytes"] = int(linha["tamanho_bytes"])
                linha["eh_duplicata"] = linha["eh_duplicata"].lower() == "true"
                arquivos.append(linha)

        return arquivos

    @staticmethod
    def comparar_manifestos(
        manifesto1: list[dict],
        manifesto2: list[dict],
        chave: str = "hash_sha256",
    ) -> dict:
        """Compara dois manifestos e retorna diferencas.

        Args:
            manifesto1: Primeiro manifesto (lista de arquivos)
            manifesto2: Segundo manifesto (lista de arquivos)
            chave: Campo a usar como chave de comparacao

        Returns:
            Dicionario com adicionados, removidos e alterados
        """
        hashes1 = {a[chave]: a for a in manifesto1}
        hashes2 = {a[chave]: a for a in manifesto2}

        chaves1 = set(hashes1.keys())
        chaves2 = set(hashes2.keys())

        adicionados = chaves2 - chaves1
        removidos = chaves1 - chaves2
        comuns = chaves1 & chaves2

        # Verificar alteracoes em campos importantes
        campos_monitorados = {"arquivo_nome", "tamanho_bytes", "bloco_logico"}
        alterados = [
            h for h in comuns
            if any(hashes1[h].get(c) != hashes2[h].get(c) for c in campos_monitorados)
        ]

        return {
            "adicionados": list(adicionados),
            "removidos": list(removidos),
            "alterados": alterados,
            "stats": {
                "total_manifesto1": len(manifesto1),
                "total_manifesto2": len(manifesto2),
                "adicionados_count": len(adicionados),
                "removidos_count": len(removidos),
                "alterados_count": len(alterados),
            },
        }
