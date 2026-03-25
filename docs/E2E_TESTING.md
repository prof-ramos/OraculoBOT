# Testes E2E - OraculoBOT

## Pré-requisitos para testes E2E

### 1. Discord Bot Token
- Obtenha um bot token no [Discord Developer Portal](https://discord.com/developers/applications)
- Adicione o token ao arquivo `.env`: `DISCORD_BOT_TOKEN=seu_token_aqui`

### 2. Guild e Channel de Teste
- Crie um servidor Discord dedicado para testes
- Crie um canal privado para testes E2E
- Anote o ID da guild e do canal:
  - `TARGET_GUILD_ID=123456789012345678`
  - `TARGET_CHANNEL_ID=123456789012345678`

### 3. Variáveis de Ambiente Opcionais
```env
# APIs de IA (para testes completos)
DEEPSEEK_API_KEY=your_deepseek_key
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key

# Configurações do bot
MODEL_ID=deepseek-chat
HISTORY_RUNS=5
TARGET_GUILD_ID=sua_guild_id
TARGET_CHANNEL_ID=seu_channel_id
MAX_MESSAGE_LENGTH=2000
ERROR_MESSAGE=Erro ao processar sua mensagem.
```

## Configuração do Ambiente de Teste

### 1. Instale dependências
```bash
uv sync
```

### 2. Configure arquivo .env
```bash
cp .env.example .env
# Edite .env com suas credenciais
```

### 3. Crie pasta de log
```bash
mkdir -p logs
```

## Testes Manuais

### Script de Teste Manual
**Localização:** `scripts/test_e2e_manual.py`

#### Como executar:
```bash
cd scripts
python test_e2e_manual.py
```

#### Funcionalidades testadas:
1. **Inicialização do bot** - Verifica se o bot inicia e entra no servidor correto
2. **Resposta a mensagens** - Envia comandos básicos e verifica respostas
3. **Resposta a menções** - Testa menções ao bot
4. **Processamento de anexos** - Envia arquivos e testa processamento
5. **Threads do Discord** - Cria e gerencia threads
6. **Limite de mensagens** - Testa truncamento de mensagens longas

#### Instruções passo a passo:
1. Execute o script manual
2. Verifique se o bot está online no Discord
3. Siga os prompts no terminal
4. Confirme se as ações são executadas corretamente no Discord

## Nota sobre Testes Automatizados

Testes E2E automatizados com mocks Discord foram removidos devido à complexidade de mockar corretamente o `discord.py`, especialmente o método `thread.typing()` que é um async context manager.

A estrutura `tests/e2e/` contém apenas fixtures (`conftest.py`) para uso futuro. Para testes automatizados, utilize os testes unitários em `tests/unit/` que cobrem toda a lógica do bot.

## Checklist de Validação E2E

### Antes dos Testes
- [ ] Bot token válido e com permissões necessárias
- [ ] Guild e channel IDs corretos
- [ ] Todas as variáveis de ambiente configuradas
- [ ] Conexão com APIs de IA ativa (opcional para testes básicos)
- [ ] Arquivos de log acessíveis

### Durante os Testes
- [ ] Bot inicia sem erros
- [ ] Bot entra no servidor correto
- [ ] Responde a mensagens em até 5 segundos
- [ ] Mensagens não excedem limite de 2000 caracteres
- [ ] Threads são criadas corretamente
- [ ] Anexos são processados sem crashes

### Pós-Testes
- [ ] Verificar arquivos de log para erros
- [ ] Confirmar que todas as actions foram executadas
- [ ] Validar que as respostas estão formatadas corretamente
- [ ] Testar cleanup de recursos

## Troubleshooting Comum

### Erros Comuns

#### 1. "Token inválido"
```
Solução:
- Verificar se o token está correto no .env
- Copiar token sem espaços extras
- Gerar novo token se necessário
```

#### 2. "Não foi possível se conectar ao servidor"
```
Solução:
- Verificar TARGET_GUILD_ID e TARGET_CHANNEL_ID
- Confirmar que o bot está convidado para o servidor
- Verificar permissões do bot no servidor
```

#### 3. "Timeout ao conectar à API"
```
Solução:
- Verificar conexão com internet
- Testar APIs individualmente
- Aumentar timeout se necessário
- Usar mocking para testes offline
```

#### 4. "Mensagens não são respondidas"
```
Solução:
- Verificar se o bot está no canal correto
- Testar mensagens com menção (@bot)
- Verificar se o bot não está em modo de manutenção
- Checar logs para erros
```

### Debug Mode

Para depuração detalhada:
```bash
# Ativar logging detalhado
export LOG_LEVEL=DEBUG
python -m pytest tests/e2e/test_bot_responses.py -v -s
```

### Logs Úteis
- `logs/bot.log`: Logs do bot
- `logs/rag.log`: Logs do sistema RAG
- `logs/api.log`: Logs das chamadas de API

## Boas Práticas

1. **Testes Isolados**: Cada teste deve rodar independentemente
2. **Mocking**: Usar mocks para Discord APIs quando possível
3. **Limpeza**: Limpar dados de teste após cada execução
4. **Versionamento**: Manter versões estáveis dos testes E2E
5. **Segurança**: Nunca commitar tokens reais no repositório

## Desenvolvimento de Novos Testes

### Criando um novo teste E2E:
```python
# tests/e2e/test_nova_funcionalidade.py
import pytest
from tests.conftest import e2e_bot, test_channel

def test_nova_funcionalidade(e2e_bot, test_channel):
    # Arrange
    message = "Comando de teste"

    # Act
    result = e2e_bot.process_message(message)

    # Assert
    assert result is not None
    assert "Resposta esperada" in result.content
```

### Melhorias Contínuas:
1. Adicionar mais casos de borda
2. Implementar testes de performance
3. Criar testes de regressão
4. Automatizar validação visual

---

*Documentação gerada automaticamente - Veja histórico do git para data de atualização*