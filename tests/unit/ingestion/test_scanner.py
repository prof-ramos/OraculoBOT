"""Testes unitarios para scanner.py - Pipeline de ingestao RAG Lote 1."""

import hashlib
import os
import tempfile
from pathlib import Path

import pytest

from oraculo_bot.ingestion.scanner import (
    ArquivoDescoberto,
    ResultadoScanner,
    ScannerLote1,
    EXTENSOES_SUPORTADAS,
    PASTAS_IGNORADAS,
)


class TestArquivoDescoberto:
    def test_create_minimal(self):
        arquivo = ArquivoDescoberto(
            caminho_absoluto="/data/test.pdf",
            caminho_relativo="test.pdf",
            arquivo_nome="test.pdf",
            extensao=".pdf",
            tamanho_bytes=1234,
            hash_sha256="abc123",
            pasta_origem="/data",
        )
        assert arquivo.caminho_absoluto == "/data/test.pdf"
        assert arquivo.arquivo_nome == "test.pdf"
        assert arquivo.eh_duplicata is False
        assert arquivo.duplicata_de is None

    def test_create_with_duplicate_flag(self):
        arquivo = ArquivoDescoberto(
            caminho_absoluto="/data/copy.pdf",
            caminho_relativo="copy.pdf",
            arquivo_nome="copy.pdf",
            extensao=".pdf",
            tamanho_bytes=1234,
            hash_sha256="abc123",
            pasta_origem="/data",
            eh_duplicata=True,
            duplicata_de="abc123",
        )
        assert arquivo.eh_duplicata is True
        assert arquivo.duplicata_de == "abc123"


class TestScannerLote1:
    @pytest.fixture
    def temp_corpus(self, tmp_path):
        """Cria estrutura de pastas temporaria para testes."""
        # Estrutura do Lote 1
        eleitoral = tmp_path / "eleitoral"
        eleitoral.mkdir()
        (eleitoral / "lei_123.pdf").write_bytes(b"conteudo lei 123")
        (eleitoral / "resolucao_tse.pdf").write_bytes(b"conteudo resolucao")

        administrativo = tmp_path / "administrativo"
        administrativo.mkdir()
        (administrativo / "decreto_456.docx").write_bytes(b"conteudo decreto")

        # Arquivo duplicado (mesmo conteudo)
        (administrativo / "copia_lei_123.pdf").write_bytes(b"conteudo lei 123")

        # Arquivos a ignorar
        ignorar = tmp_path / ".git"
        ignorar.mkdir()
        (ignorar / "config").write_bytes(b"git config")

        return tmp_path

    def test_init(self, temp_corpus):
        scanner = ScannerLote1(str(temp_corpus))
        assert scanner.raiz_corpus == temp_corpus.resolve()
        assert scanner.extensoes == EXTENSOES_SUPORTADAS
        assert scanner.pastas_ignoradas == PASTAS_IGNORADAS

    def test_init_custom_extensoes(self, temp_corpus):
        extensoes = {".pdf", ".txt"}
        scanner = ScannerLote1(str(temp_corpus), extensoes=extensoes)
        assert scanner.extensoes == extensoes

    def test_calcular_hash_sha256(self, temp_corpus):
        scanner = ScannerLote1(str(temp_corpus))
        arquivo = temp_corpus / "eleitoral" / "lei_123.pdf"
        hash_result = scanner.calcular_hash_sha256(arquivo)

        # Verificar que e um hash SHA-256 valido (64 chars hex)
        assert len(hash_result) == 64
        assert all(c in "0123456789abcdef" for c in hash_result)

    def test_calcular_hash_sha256_conforme_esperado(self, temp_corpus):
        scanner = ScannerLote1(str(temp_corpus))
        arquivo = temp_corpus / "eleitoral" / "lei_123.pdf"
        conteudo = b"conteudo lei 123"
        hash_esperado = hashlib.sha256(conteudo).hexdigest()

        hash_result = scanner.calcular_hash_sha256(arquivo)
        assert hash_result == hash_esperado

    def test_inferir_bloco_logico_eleitoral(self, temp_corpus):
        scanner = ScannerLote1(str(temp_corpus))
        bloco = scanner.inferir_bloco_logico("/data/eleitoral/leis")
        assert bloco == "eleitoral"

    def test_inferir_bloco_logico_administrativo(self, temp_corpus):
        scanner = ScannerLote1(str(temp_corpus))
        bloco = scanner.inferir_bloco_logico("/data/administrativo/decretos")
        assert bloco == "administrativo"

    def test_inferir_bloco_logico_eca(self, temp_corpus):
        scanner = ScannerLote1(str(temp_corpus))
        bloco = scanner.inferir_bloco_logico("/data/eca_e_educacao/eca")
        assert bloco == "eca"

    def test_inferir_bloco_logico_desconhecido(self, temp_corpus):
        scanner = ScannerLote1(str(temp_corpus))
        bloco = scanner.inferir_bloco_logico("/data/outra_pasta")
        assert bloco == "desconhecido"

    def test_escanear_descobre_arquivos(self, temp_corpus):
        scanner = ScannerLote1(str(temp_corpus))
        resultado = scanner.escanear()

        # 2 PDFs originais + 1 DOCX + 1 duplicata = 4 total
        assert resultado.total_arquivos == 4
        assert resultado.stats["total_unicos"] == 3

        # Verificar que arquivos foram descobertos
        nomes = [a.arquivo_nome for a in resultado.arquivos]
        assert "lei_123.pdf" in nomes
        assert "resolucao_tse.pdf" in nomes
        assert "decreto_456.docx" in nomes

    def test_escanear_detecta_duplicatas(self, temp_corpus):
        scanner = ScannerLote1(str(temp_corpus))
        resultado = scanner.escanear()

        # lei_123.pdf e copia_lei_123.pdf tem mesmo conteudo
        # Entao total_arquivos = 4 (3 unicos + 1 duplicata)
        assert resultado.total_arquivos == 4
        assert resultado.total_duplicatas >= 1

        # Verificar que duplicata foi marcada
        duplicados = [a for a in resultado.arquivos if a.eh_duplicata]
        assert len(duplicados) >= 1

    def test_escanear_ignora_pastas_git(self, temp_corpus):
        scanner = ScannerLote1(str(temp_corpus))
        resultado = scanner.escanear()

        # Verificar que nao escaneou .git
        caminhos = [a.caminho_absoluto for a in resultado.arquivos]
        assert not any(".git" in c for c in caminhos)

    def test_escanear_filtra_por_extensao(self, temp_corpus):
        # Criar arquivo nao suportado
        (temp_corpus / "eleitoral" / "imagem.png").write_bytes(b"imagem")

        scanner = ScannerLote1(str(temp_corpus))
        resultado = scanner.escanear()

        # PNG nao deve aparecer
        extensoes = [a.extensao for a in resultado.arquivos]
        assert ".png" not in extensoes

    def test_escanear_pasta_especifica(self, temp_corpus):
        scanner = ScannerLote1(str(temp_corpus))
        resultado = scanner.escanear(pastas_alvo=["eleitoral"])

        # So arquivos da pasta eleitoral
        for arquivo in resultado.arquivos:
            assert "eleitoral" in arquivo.caminho_relativo

    def test_escanear_preserva_caminho_relativo(self, temp_corpus):
        scanner = ScannerLote1(str(temp_corpus))
        resultado = scanner.escanear()

        # Verificar que caminho_relativo esta correto
        for arquivo in resultado.arquivos:
            assert arquivo.caminho_relativo.startswith("eleitoral") or \
                   arquivo.caminho_relativo.startswith("administrativo")

    def test_escanear_gera_stats(self, temp_corpus):
        scanner = ScannerLote1(str(temp_corpus))
        resultado = scanner.escanear()

        assert "total_arquivos" in resultado.stats
        assert "total_unicos" in resultado.stats
        assert "extensoes_encontradas" in resultado.stats
        assert "duracao_segundos" in resultado.stats

    def test_escanear_pasta_inexistente(self, temp_corpus):
        scanner = ScannerLote1(str(temp_corpus))
        resultado = scanner.escanear(pastas_alvo=["pasta_inexistente"])

        assert len(resultado.erros) >= 1
        assert any("nao existe" in e.lower() for e in resultado.erros)


class TestConstantes:
    def test_extensoes_suptadas_contem_principais(self):
        assert ".pdf" in EXTENSOES_SUPORTADAS
        assert ".docx" in EXTENSOES_SUPORTADAS
        assert ".txt" in EXTENSOES_SUPORTADAS
        assert ".md" in EXTENSOES_SUPORTADAS

    def test_pastas_ignoradas_contem_principais(self):
        assert ".git" in PASTAS_IGNORADAS
        assert "__pycache__" in PASTAS_IGNORADAS
        assert ".venv" in PASTAS_IGNORADAS
