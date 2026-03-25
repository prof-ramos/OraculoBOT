# Testes E2E do OraculoBOT

## Status

Testes E2E automatizados com mocks do Discord foram removidos devido à complexidade de mockar corretamente o `discord.py`, especialmente o método `thread.typing()` que é um async context manager.

## Alternativas Recomendadas

### 1. Teste Manual (Recomendado)

Use o script `scripts/test_e2e_manual.py` para testes E2E reais:

```bash
# Dry-run (valida config sem iniciar bot)
python scripts/test_e2e_manual.py --dry-run

# Teste completo
python scripts/test_e2e_manual.py
```

Veja documentação completa em `docs/E2E_TESTING.md`.

### 2. Testes Unitários

Testes unitários em `tests/unit/` cobrem a lógica do bot:

```bash
uv run pytest tests/unit/ -v
```

### 3. Teste Manual no Discord

Para testes E2E simples:
1. Inicie o bot: `python -m oraculo_bot`
2. Envie mensagens no canal configurado
3. Observe as respostas e logs

## Por que testes E2E automatizados foram removidos?

Mockar o `discord.py` corretamente requer:
- `spec=` em todos os mocks para passar `isinstance()` checks
- Async context managers funcionais para `thread.typing()`
- Gerenciamento complexo de estados do Discord

O esforço para manter esses mocks funcionando supera o benefício, considerando que:
- Testes unitários já cobrem a lógica do bot
- Testes manuais são mais realistas para validação E2E
- O script `test_e2e_manual.py` facilita testes manuais estruturados
