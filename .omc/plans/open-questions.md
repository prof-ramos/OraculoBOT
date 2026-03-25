# Open Questions

Este arquivo rastreia perguntas nao resolvidas, decisoes adiadas para o usuario e itens que precisam de esclarecimento antes ou durante a execucao.

---

## [Supabase Integration] - 2025-03-25 (Revisao 3 - ITERACAO 3)

### Decisoes tomadas na ITERACAO 3 (CORRECOES CRITICAS):

1. **[RESOLVIDO] API invalida `agent.memory.messages`** — Removida manipulacao de memoria. Agno usa `add_history_to_context=True` + `session_id` nativamente.

2. **[RESOLVIDO] Hook nunca chamado** — Adicionado hook em `bot.py:_process_message()` para chamar `save_session_history()` apos `arun()`.

3. **[RESOLVIDO] agent_factory ineficiente** — Removido padrao factory. Instancia unica do Agent e reutilizada com `session_id` dinamico.

4. **[RESOLVIDO] Tratamento de erro DB** — Todas as operacoes DAO tem try/except com fallback para memoria.

5. **[RESOLVIDO] Limpeza de sessoes antigas** — Implementado `cleanup_old_sessions(days=30)` no DAO.

6. **[RESOLVIDO] Deteccao de modo** — Adicionado Passo 9 opcional com `mode_detector.py` e keywords para cada modo.

7. **[RESOLVIDO] Assinatura create_agent()** — Mantida assinatura original para nao quebrar codigo existente. Gerenciamento de sessao via funcoes separadas.

### Decisoes tomadas na ITERACAO 2:

1. **[RESOLVIDO] Dupla camada de persistencia** — Removido completamente PostgresDb do Agno. SessionDAO e agora a UNICA camada.

2. **[RESOLVIDO] Race condition** — `get_or_create_session()` implementado com `INSERT ... ON CONFLICT` para thread-safety.

### Pendente para execucao:

- [ ] **[USER] Periodo de retencao**: Confirmar se 30 dias e o periodo adequado para limpeza de sessoes antigas (Passo 10 / cleanup_old_sessions)
- [ ] **[USER] Deteccao de modo**: Decidir se implementa deteccao automatica (Passo 9 - opcional) ou usa modo fixo "estudo"
- [ ] Considerar adiciona Alembic para migrations se schema evoluir (follow-up ADR)

---

