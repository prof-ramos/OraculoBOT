"""Testes unitarios para manifest.py - Pipeline de ingestao RAG Lote 1."""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from oraculo_bot.ingestion.scanner import ArquivoDescoberto, ResultadoScanner
from oraculo_bot.ingestion.manifest import (
    ManifestoWriter,
    ManifestoReader,
)


class TestManifestoWriter:
    @pytest.fixture
    def resultado_scanner(self):
        """Cria resultado de scanner para testes."""
        arquivos = [
            ArquivoDescoberto(
                caminho_absoluto="/data/eleitoral/lei_123.pdf",
                caminho_relativo="eleitoral/lei_123.pdf",
                arquivo_nome="lei_123.pdf",
                extensao=".pdf",
                tamanho_bytes=1234,
                hash_sha256="abc123",
                pasta_origem="/data/eleitoral",
                bloco_logico="eleitoral",
            ),
            ArquivoDescoberto(
                caminho_absoluto="/data/eleitoral/resolucao_tse.pdf",
                caminho_relativo="eleitoral/resolucao_tse.pdf",
                arquivo_nome="resolucao_tse.pdf",
                extensao=".pdf",
                tamanho_bytes=5678,
                hash_sha256="def456",
                pasta_origem="/data/eleitoral",
                bloco_logico="eleitoral",
                eh_duplicata=True,
                duplicata_de="abc123",
            ),
        ]

        return ResultadoScanner(
            run_key="lote1_v1_eleitoral",
            raiz_corpus="/data",
            blocos_logicos=["eleitoral"],
            arquivos=arquivos,
            total_arquivos=2,
            total_duplicatas=1,
            started_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            finished_at=datetime(2024, 1, 1, 10, 0, 5, tzinfo=timezone.utc),
            stats={"duracao_segundos": 5.0},
        )

    def test_init(self, tmp_path):
        writer = ManifestoWriter(str(tmp_path))
        assert writer.diretorio_saida == tmp_path

    def test_init_cria_diretorio(self):
        with tempfile.TemporaryDirectory() as tmp:
            novo_dir = Path(tmp) / "manifestos"
            ManifestoWriter(str(novo_dir))
            assert novo_dir.exists()

    def test_escrever_csv(self, resultado_scanner, tmp_path):
        writer = ManifestoWriter(str(tmp_path))
        caminho = writer.escrever_csv(resultado_scanner)

        assert caminho.exists()
        assert caminho.suffix == ".csv"

        # Verificar conteudo
        with open(caminho, "r", encoding="utf-8") as f:
            linhas = f.readlines()
            assert len(linhas) == 3  # header + 2 arquivos

            # Verificar header
            assert "caminho_absoluto" in linhas[0]
            assert "hash_sha256" in linhas[0]

    def test_escrever_jsonl(self, resultado_scanner, tmp_path):
        writer = ManifestoWriter(str(tmp_path))
        caminho = writer.escrever_jsonl(resultado_scanner)

        assert caminho.exists()
        assert caminho.suffix == ".jsonl"

        # Verificar conteudo
        with open(caminho, "r", encoding="utf-8") as f:
            linhas = f.readlines()

            # Primeira linha e metadados
            meta = json.loads(linhas[0])
            assert meta.get("_meta") is True
            assert meta["run_key"] == "lote1_v1_eleitoral"

            # Segunda e terceira sao arquivos
            arquivo1 = json.loads(linhas[1])
            assert "caminho_absoluto" in arquivo1
            assert arquivo1["_run_key"] == "lote1_v1_eleitoral"

    def test_escrever_jsonl_sem_metadados(self, resultado_scanner, tmp_path):
        writer = ManifestoWriter(str(tmp_path))
        caminho = writer.escrever_jsonl(resultado_scanner, incluir_metadados=False)

        with open(caminho, "r", encoding="utf-8") as f:
            linhas = f.readlines()

            # Primeira linha nao deve ser metadados
            primeiro = json.loads(linhas[0])
            assert primeiro.get("_meta") is None

    def test_escrever_resumo(self, resultado_scanner, tmp_path):
        writer = ManifestoWriter(str(tmp_path))
        caminho = writer.escrever_resumo(resultado_scanner)

        assert caminho.exists()
        assert caminho.suffix == ".json"

        with open(caminho, "r", encoding="utf-8") as f:
            resumo = json.load(f)

        assert resumo["run_key"] == "lote1_v1_eleitoral"
        assert resumo["total_arquivos"] == 2

    def test_nome_arquivo_personalizado(self, resultado_scanner, tmp_path):
        writer = ManifestoWriter(str(tmp_path))
        caminho_custom = tmp_path / "custom_manifest.jsonl"
        caminho = writer.escrever_jsonl(resultado_scanner, arquivo_saida=str(caminho_custom))

        assert caminho == caminho_custom


class TestManifestoReader:
    @pytest.fixture
    def manifesto_jsonl(self, tmp_path):
        """Cria manifesto JSONL de teste."""
        caminho = tmp_path / "test.jsonl"

        linhas = [
            json.dumps({
                "_meta": True,
                "run_key": "test_run",
                "raiz_corpus": "/data",
            }),
            json.dumps({
                "caminho_absoluto": "/data/test.pdf",
                "caminho_relativo": "test.pdf",
                "arquivo_nome": "test.pdf",
                "extensao": ".pdf",
                "tamanho_bytes": 1234,
                "hash_sha256": "abc123",
                "pasta_origem": "/data",
                "eh_duplicata": False,
                "duplicata_de": None,
                "_run_key": "test_run",
            }),
        ]

        with open(caminho, "w", encoding="utf-8") as f:
            f.write("\n".join(linhas))

        return caminho

    @pytest.fixture
    def manifesto_csv(self, tmp_path):
        """Cria manifesto CSV de teste."""
        caminho = tmp_path / "test.csv"

        conteudo = """caminho_absoluto,caminho_relativo,arquivo_nome,extensao,tamanho_bytes,hash_sha256,pasta_origem,eh_duplicata,duplicata_de
/data/test.pdf,test.pdf,test.pdf,.pdf,1234,abc123,/data,False,
"""

        with open(caminho, "w", encoding="utf-8") as f:
            f.write(conteudo)

        return caminho

    def test_ler_jsonl(self, manifesto_jsonl):
        metadados, arquivos = ManifestoReader.ler_jsonl(str(manifesto_jsonl))

        assert metadados["run_key"] == "test_run"
        assert len(arquivos) == 1
        assert arquivos[0]["caminho_absoluto"] == "/data/test.pdf"

    def test_ler_csv(self, manifesto_csv):
        arquivos = ManifestoReader.ler_csv(str(manifesto_csv))

        assert len(arquivos) == 1
        assert arquivos[0]["caminho_absoluto"] == "/data/test.pdf"
        assert arquivos[0]["tamanho_bytes"] == 1234
        assert arquivos[0]["eh_duplicata"] is False

    def test_comparar_manifestos_iguais(self):
        manifesto = [
            {"hash_sha256": "abc", "arquivo_nome": "test1.pdf"},
            {"hash_sha256": "def", "arquivo_nome": "test2.pdf"},
        ]

        resultado = ManifestoReader.comparar_manifestos(manifesto, manifesto)

        assert len(resultado["adicionados"]) == 0
        assert len(resultado["removidos"]) == 0
        assert len(resultado["alterados"]) == 0

    def test_comparar_manifestos_com_adicoes(self):
        manifesto1 = [
            {"hash_sha256": "abc", "arquivo_nome": "test1.pdf"},
        ]
        manifesto2 = [
            {"hash_sha256": "abc", "arquivo_nome": "test1.pdf"},
            {"hash_sha256": "def", "arquivo_nome": "test2.pdf"},
        ]

        resultado = ManifestoReader.comparar_manifestos(manifesto1, manifesto2)

        assert "def" in resultado["adicionados"]
        assert len(resultado["removidos"]) == 0

    def test_comparar_manifestos_com_remocoes(self):
        manifesto1 = [
            {"hash_sha256": "abc", "arquivo_nome": "test1.pdf"},
            {"hash_sha256": "def", "arquivo_nome": "test2.pdf"},
        ]
        manifesto2 = [
            {"hash_sha256": "abc", "arquivo_nome": "test1.pdf"},
        ]

        resultado = ManifestoReader.comparar_manifestos(manifesto1, manifesto2)

        assert "def" in resultado["removidos"]
        assert len(resultado["adicionados"]) == 0

    def test_comparar_manifestos_com_alteracoes(self):
        manifesto1 = [
            {"hash_sha256": "abc", "arquivo_nome": "test1.pdf", "tamanho_bytes": 1000},
        ]
        manifesto2 = [
            {"hash_sha256": "abc", "arquivo_nome": "test2.pdf", "tamanho_bytes": 2000},  # Mesmo hash, nome diferente
        ]

        resultado = ManifestoReader.comparar_manifestos(manifesto1, manifesto2)

        # Mesmo hash, mas campos alterados
        assert "abc" in resultado["alterados"]

    def test_comparar_manifestos_stats(self):
        manifesto1 = [{"hash_sha256": f"hash{i}"} for i in range(5)]
        manifesto2 = [{"hash_sha256": f"hash{i}"} for i in range(3, 8)]

        resultado = ManifestoReader.comparar_manifestos(manifesto1, manifesto2)

        assert resultado["stats"]["total_manifesto1"] == 5
        assert resultado["stats"]["total_manifesto2"] == 5
