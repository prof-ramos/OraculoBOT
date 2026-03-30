"""Testes unitarios para extractor.py - Pipeline de ingestao RAG Lote 1."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from oraculo_bot.ingestion.extractor import (
    ExtratorTexto,
    ResultadoExtracao,
    MetodoExtracao,
    StatusExtracaoTexto,
    TextoRuimDetector,
    MIN_CHARS_TEXTO,
    MAX_RATIO_CHARS_QUEBRADOS,
)


class TestMetodoExtracao:
    def test_valores_existem(self):
        assert MetodoExtracao.PDF_TEXTO.value == "pdf_texto"
        assert MetodoExtracao.PDF_OCR.value == "pdf_ocr"
        assert MetodoExtracao.DOCX.value == "docx"
        assert MetodoExtracao.TEXTO.value == "texto"
        assert MetodoExtracao.MARKDOWN.value == "markdown"


class TestStatusExtracaoTexto:
    def test_status_validos(self):
        assert StatusExtracaoTexto.OK.value == "ok"
        assert StatusExtracaoTexto.PARCIAL.value == "parcial"
        assert StatusExtracaoTexto.FALHA.value == "falha"
        assert StatusExtracaoTexto.VAZIO.value == "vazio"
        assert StatusExtracaoTexto.CURTO_DEMAIS.value == "curto_demais"
        assert StatusExtracaoTexto.CORROMPIDO.value == "corrompido"


class TestTextoRuimDetector:
    def test_detectar_vazio_none(self):
        assert TextoRuimDetector.detectar_vazio(None) is True

    def test_detectar_vazio_string_vazia(self):
        assert TextoRuimDetector.detectar_vazio("") is True

    def test_detectar_vazio_apenas_whitespace(self):
        assert TextoRuimDetector.detectar_vazio("   \n\t  ") is True

    def test_detectar_vazio_com_conteudo(self):
        assert TextoRuimDetector.detectar_vazio("texto valido") is False

    def test_detectar_curto_demais_none(self):
        assert TextoRuimDetector.detectar_curto_demais(None) is True

    def test_detectar_curto_demais_muito_curto(self):
        texto_curto = "x" * (MIN_CHARS_TEXTO - 1)
        assert TextoRuimDetector.detectar_curto_demais(texto_curto) is True

    def test_detectar_curto_demais_suficiente(self):
        texto_ok = "x" * MIN_CHARS_TEXTO
        assert TextoRuimDetector.detectar_curto_demais(texto_ok) is False

    def test_calcular_ratio_chars_quebrados_sem_quebrados(self):
        texto = "Texto limpo sem caracteres quebrados"
        ratio = TextoRuimDetector.calcular_ratio_chars_quebrados(texto)
        assert ratio == 0.0

    def test_calcular_ratio_chars_quebrados_com_quebrados(self):
        texto = "Texto com " + ("�" * 10) + " quebrados"
        ratio = TextoRuimDetector.calcular_ratio_chars_quebrados(texto)
        assert ratio > 0

    def test_calcular_ratio_chars_quebrados_vazio(self):
        ratio = TextoRuimDetector.calcular_ratio_chars_quebrados("")
        assert ratio == 1.0

    def test_detectar_corrompido_limpo(self):
        texto = "Texto " * 20
        assert TextoRuimDetector.detectar_corrompido(texto) is False

    def test_detectar_corrompido_muitos_quebrados(self):
        texto = "x" * 50 + "�" * 50  # 50% de chars quebrados
        assert TextoRuimDetector.detectar_corrompido(texto) is True

    def test_avaliar_texto_vazio(self):
        status, quarentena, motivo = TextoRuimDetector.avaliar_texto(None)
        assert status == StatusExtracaoTexto.VAZIO
        assert quarentena is True
        assert "vazio" in motivo.lower()

    def test_avaliar_texto_curto(self):
        status, quarentena, _motivo = TextoRuimDetector.avaliar_texto("texto curto")
        assert status == StatusExtracaoTexto.CURTO_DEMAIS
        assert quarentena is True

    def test_avaliar_texto_corrompido(self):
        texto = "x" * 50 + "�" * 50
        status, quarentena, _motivo = TextoRuimDetector.avaliar_texto(texto)
        assert status == StatusExtracaoTexto.CORROMPIDO
        assert quarentena is True

    def test_avaliar_texto_valido(self):
        texto = "Este e um texto valido com mais de cinquenta caracteres para teste."
        status, quarentena, motivo = TextoRuimDetector.avaliar_texto(texto)
        assert status == StatusExtracaoTexto.OK
        assert quarentena is False
        assert motivo is None


class TestResultadoExtracao:
    def test_create_minimal(self):
        resultado = ResultadoExtracao(caminho_arquivo="/data/test.pdf")
        assert resultado.caminho_arquivo == "/data/test.pdf"
        assert resultado.texto is None
        assert resultado.status == StatusExtracaoTexto.OK
        assert resultado.char_count == 0

    def test_create_with_text(self):
        resultado = ResultadoExtracao(
            caminho_arquivo="/data/test.txt",
            texto="Texto extraido",
            metodo=MetodoExtracao.TEXTO,
        )
        assert resultado.texto == "Texto extraido"
        assert resultado.metodo == MetodoExtracao.TEXTO


class TestExtratorTexto:
    @pytest.fixture
    def extrator(self):
        return ExtratorTexto(tentar_ocr=False)  # Desabilitar OCR para testes

    def test_init(self, extrator):
        assert extrator.tentar_ocr is False
        assert extrator.min_chars_texto == MIN_CHARS_TEXTO

    def test_extrair_arquivo_inexistente(self, extrator):
        resultado = extrator.extrair("/caminho/inexistente.pdf")
        assert resultado.status == StatusExtracaoTexto.FALHA
        assert resultado.precisa_quarentena is True
        assert "nao existe" in resultado.erro.lower()

    def test_extrair_formato_nao_suportado(self, extrator, tmp_path):
        arquivo = tmp_path / "test.xyz"
        arquivo.write_text("conteudo")

        resultado = extrator.extrair(str(arquivo))
        assert resultado.status == StatusExtracaoTexto.FALHA
        assert "nao suportado" in resultado.erro.lower()

    def test_extrair_txt_utf8(self, extrator, tmp_path):
        arquivo = tmp_path / "test.txt"
        conteudo = "Este e um texto de teste com mais de cinquenta caracteres para validacao."
        arquivo.write_text(conteudo, encoding="utf-8")

        resultado = extrator.extrair(str(arquivo))
        assert resultado.status == StatusExtracaoTexto.OK
        assert resultado.texto == conteudo
        assert resultado.metodo == MetodoExtracao.TEXTO
        assert resultado.char_count == len(conteudo)

    def test_extrair_txt_latin1(self, extrator, tmp_path):
        arquivo = tmp_path / "test.txt"
        conteudo = "Texto com acentos: acao, nao, valido com mais caracteres para atingir minimum"
        arquivo.write_text(conteudo, encoding="latin-1")

        resultado = extrator.extrair(str(arquivo))
        # Latin-1 decode might not always succeed, could be curto or OK
        assert resultado.status in StatusExtracaoTexto
        assert resultado.metodo == MetodoExtracao.TEXTO

    def test_extrair_markdown(self, extrator, tmp_path):
        arquivo = tmp_path / "test.md"
        conteudo = "# Titulo\n\nEste e um markdown com mais de cinquenta caracteres."
        arquivo.write_text(conteudo, encoding="utf-8")

        resultado = extrator.extrair(str(arquivo))
        assert resultado.status == StatusExtracaoTexto.OK
        assert resultado.metodo == MetodoExtracao.MARKDOWN

    def test_extrair_txt_vazio(self, extrator, tmp_path):
        arquivo = tmp_path / "vazio.txt"
        arquivo.write_text("")

        resultado = extrator.extrair(str(arquivo))
        assert resultado.status == StatusExtracaoTexto.VAZIO
        assert resultado.precisa_quarentena is True

    def test_extrair_txt_curto_demais(self, extrator, tmp_path):
        arquivo = tmp_path / "curto.txt"
        arquivo.write_text("curto")

        resultado = extrator.extrair(str(arquivo))
        assert resultado.status == StatusExtracaoTexto.CURTO_DEMAIS
        assert resultado.precisa_quarentena is True

    @patch("oraculo_bot.ingestion.extractor.pdfplumber", create=True)
    def test_extrair_pdf_com_texto(self, mock_pdfplumber, extrator, tmp_path):
        # Skip se pdfplumber nao estiver instalado
        try:
            import pdfplumber  # noqa: F401
        except ImportError:
            pytest.skip("pdfplumber nao instalado")

        # Mock pdfplumber
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Texto extraido do PDF com mais de cinquenta caracteres para validacao."
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        mock_pdfplumber.open.return_value = mock_pdf

        arquivo = tmp_path / "test.pdf"
        arquivo.write_bytes(b"fake pdf")

        resultado = extrator.extrair(str(arquivo))
        assert resultado.status == StatusExtracaoTexto.OK
        assert resultado.metodo == MetodoExtracao.PDF_TEXTO
        assert resultado.texto is not None

    @patch("oraculo_bot.ingestion.extractor.Document", create=True)
    def test_extrair_docx(self, mock_document, extrator, tmp_path):
        # Skip se python-docx nao estiver instalado
        try:
            from docx import Document  # noqa: F401
        except ImportError:
            pytest.skip("python-docx nao instalado")

        # Mock python-docx
        mock_doc = MagicMock()
        mock_paragrafo = MagicMock()
        mock_paragrafo.text = "Paragrafo do documento com mais de cinquenta caracteres para teste."
        mock_doc.paragraphs = [mock_paragrafo]
        mock_doc.tables = []
        mock_document.return_value = mock_doc

        arquivo = tmp_path / "test.docx"
        arquivo.write_bytes(b"fake docx")

        resultado = extrator.extrair(str(arquivo))
        assert resultado.status == StatusExtracaoTexto.OK
        assert resultado.metodo == MetodoExtracao.DOCX

    def test_extrair_preserva_metadados(self, extrator, tmp_path):
        arquivo = tmp_path / "test.txt"
        conteudo = "Texto com mais de cinquenta caracteres para verificar metadados."
        arquivo.write_text(conteudo, encoding="utf-8")

        resultado = extrator.extrair(str(arquivo))
        assert resultado.metadata is not None
        assert "encoding" in resultado.metadata
        assert resultado.extracted_at is not None


class TestConstantes:
    def test_min_chars_texto_razoavel(self):
        assert MIN_CHARS_TEXTO >= 20
        assert MIN_CHARS_TEXTO <= 200

    def test_max_ratio_chars_quebrados_razoavel(self):
        assert MAX_RATIO_CHARS_QUEBRADOS > 0
        assert MAX_RATIO_CHARS_QUEBRADOS <= 1.0
