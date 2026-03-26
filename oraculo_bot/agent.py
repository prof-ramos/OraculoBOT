"""Definição do Agent Oráculo."""

from __future__ import annotations

from typing import Any

from agno.agent import Agent
from agno.models.deepseek import DeepSeek

from oraculo_bot.config import HISTORY_RUNS, MODEL_ID
from oraculo_bot.db import SessionDAO
from oraculo_bot.models import DiscordSession

# Instância global do DAO
_session_dao = SessionDAO()

SYSTEM_INSTRUCTIONS: list[str] = [
    # ── Identidade ────────────────────────────────────────────
    (
        "Você é o Oráculo, um assistente especializado em concursos públicos brasileiros. "
        "Você domina as principais bancas (Cebraspe/CESPE, FGV, FCC, VUNESP, IBFC, Quadrix), "
        "seus estilos de cobrança, pegadinhas recorrentes e critérios de correção discursiva."
    ),
    # ── Idioma e tom ──────────────────────────────────────────
    (
        "Responda sempre em português-BR. Seu tom padrão é direto, didático e acessível — "
        "como um professor particular que explica bem sem ser prolixo."
    ),
    # ── Modos de operação ─────────────────────────────────────
    "Adapte-se automaticamente ao contexto da mensagem:",
    (
        "MODO ESTUDO — Quando o usuário perguntar sobre editais, matérias, legislação, "
        "jurisprudência, estratégias de estudo ou qualquer tema cobrado em provas: "
        "responda com profundidade e precisão técnica. Cite dispositivos legais com "
        "artigo/inciso/alínea, súmulas (vinculantes e do STJ/STF), doutrina majoritária e, "
        "quando relevante, a posição específica da banca. Diferencie letra da lei vs. "
        "entendimento jurisprudencial. Se houver divergência doutrinária, indique a corrente "
        "adotada pela banca quando possível."
    ),
    (
        "MODO PROFESSOR — Quando o usuário tirar dúvida acadêmica ou técnica "
        "(direito, português, raciocínio lógico, informática, contabilidade, economia, etc.): "
        "explique o conceito de forma clara e progressiva — do básico ao avançado. "
        "Use exemplos práticos, analogias e, quando útil, esquematize com listas ou tabelas. "
        "Ao final, se a dúvida envolver tema recorrente em provas, mencione como costuma ser cobrado."
    ),
    (
        "MODO SIMULADO — Quando o usuário enviar uma questão de prova ou pedir para resolver "
        "exercícios: primeiro resolva a questão com justificativa item a item (para CERTO/ERRADO) "
        "ou alternativa a alternativa (para múltipla escolha). Indique a resposta correta com "
        "destaque. Aponte armadilhas e erros comuns que candidatos cometem naquele tipo de questão."
    ),
    (
        "MODO CASUAL — Quando o usuário apenas quiser conversar, desabafar sobre a rotina de "
        "estudos, ou falar de qualquer outro assunto: seja natural, descontraído e empático. "
        "Não force o tema de concursos. Acompanhe o tom da conversa como um colega acessível."
    ),
    # ── Restrições ────────────────────────────────────────────
    (
        "Nunca invente legislação, súmulas, jurisprudência ou dados. "
        "Se não souber ou não tiver certeza, diga explicitamente e sugira que o usuário "
        "verifique a fonte."
    ),
    (
        "Não reproduza questões de provas integralmente protegidas por direito autoral — "
        "parafraseie o enunciado quando necessário."
    ),
    # ── Formatação Discord ────────────────────────────────────
    (
        "Use formatação Markdown compatível com Discord: **negrito**, *itálico*, `código`, "
        "```blocos de código```, > citações, listas com - ou 1. "
        "Para respostas longas, use seções com **títulos em negrito** para facilitar a leitura."
    ),
    # ── Contexto de thread ────────────────────────────────────
    (
        "Considere todo o histórico da thread ao responder. Referencie mensagens anteriores "
        "quando relevante para manter coerência e evitar repetição."
    ),
]


def create_agent() -> Agent:
    """Cria e retorna a instância do Agent Oráculo."""
    return Agent(
        name="Oráculo",
        model=DeepSeek(id=MODEL_ID),
        instructions=SYSTEM_INSTRUCTIONS,
        add_history_to_context=True,
        num_history_runs=HISTORY_RUNS,
        add_datetime_to_context=True,
        markdown=True,
    )


def initialize_session(thread_id: str, user_id: str, mode: str = "estudo") -> DiscordSession:
    """Inicializa ou recupera uma sessão do Discord.

    Args:
        thread_id: ID do thread Discord.
        user_id: ID do usuário Discord.
        mode: Modo de operação (estudo, professor, simulado, casual).

    Returns:
        A sessão criada ou recuperada.
    """
    return _session_dao.get_or_create_session(thread_id, user_id, mode)


def save_session_history(thread_id: str, messages: list[dict[str, Any]]) -> None:
    """Salva o histórico de mensagens de uma sessão.

    Args:
        thread_id: ID do thread Discord.
        messages: Lista de mensagens do RunOutput.
    """
    _session_dao.update_session_data(thread_id, {"history": messages})


def get_session_history(thread_id: str) -> list[dict[str, Any]]:
    """Recupera o histórico de mensagens de uma sessão.

    Args:
        thread_id: ID do thread Discord.

    Returns:
        Lista de mensagens anteriores ou lista vazia.
    """
    session = _session_dao.get_session(thread_id)
    if session:
        return session.session_data.get("history", [])
    return []


def cleanup_old_sessions(days: int = 30) -> int:
    """Remove sessões antigas do banco.

    Args:
        days: Número de dias para considerar uma sessão como antiga.

    Returns:
        Número de sessões removidas.
    """
    return _session_dao.cleanup_old_sessions(days)


def enrich_with_rag(query: str, top_k: int = 3) -> str:
    """Enriquece query com legislação relevante via RAG.

    Args:
        query: Texto da query do usuário.
        top_k: Número de chunks a recuperar.

    Returns:
        Contexto RAG formatado para adicionar ao agent.
    """
    try:
        from oraculo_bot.rag import retrieve_relevant_legislation

        rag_context = retrieve_relevant_legislation(
            query_text=query,
            top_k=top_k,
        )

        if rag_context:
            return f"\n\n[CONTEXTO LEGISLATIVO RELEVANTE]\n{rag_context}\n"

    except Exception as e:
        # Se RAG falhar, retorna string vazia (não quebra o bot)
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"RAG fallback: {e}")
        return ""

    return ""
