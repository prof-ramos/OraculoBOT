"""Testes unitários para views.py - ConfirmationView."""

from unittest.mock import Mock, MagicMock, AsyncMock
import pytest

from oraculo_bot.views import ConfirmationView


class TestConfirmationViewInit:
    """Testes para inicialização do ConfirmationView."""

    def test_init_default_timeout(self):
        """Deve usar timeout padrão de 60.0."""
        view = ConfirmationView()
        assert view.timeout == 60.0
        assert view.value is None

    def test_init_custom_timeout(self):
        """Deve aceitar timeout customizado."""
        view = ConfirmationView(timeout=30.0)
        assert view.timeout == 30.0
        assert view.value is None

    def test_init_value_initially_none(self):
        """Deve inicializar value como None."""
        view = ConfirmationView()
        assert view.value is None

    def test_init_has_two_buttons(self):
        """Deve ter 2 botões (confirm e cancel)."""
        view = ConfirmationView()
        assert len(view.children) == 2

    def test_init_not_finished(self):
        """View não deve estar finalizada ao criar."""
        view = ConfirmationView()
        assert not view.is_finished()


class TestConfirmationButtons:
    """Testes para botões confirm e cancel."""

    def test_confirm_button_exists(self):
        """Deve ter botão confirmar."""
        view = ConfirmationView()
        confirm_buttons = [b for b in view.children if hasattr(b, 'label') and 'Confirm' in b.label]
        assert len(confirm_buttons) == 1
        assert confirm_buttons[0].style.name == 'primary'

    def test_cancel_button_exists(self):
        """Deve ter botão cancelar."""
        view = ConfirmationView()
        cancel_buttons = [b for b in view.children if hasattr(b, 'label') and 'Cancel' in b.label]
        assert len(cancel_buttons) == 1
        assert cancel_buttons[0].style.name == 'secondary'

    def test_confirm_button_has_emoji(self):
        """Botão confirmar deve ter emoji ✅."""
        view = ConfirmationView()
        confirm_buttons = [b for b in view.children if hasattr(b, 'label') and 'Confirm' in b.label]
        assert '✅' in confirm_buttons[0].label

    def test_cancel_button_has_emoji(self):
        """Botão cancelar deve ter emoji ❌."""
        view = ConfirmationView()
        cancel_buttons = [b for b in view.children if hasattr(b, 'label') and 'Cancel' in b.label]
        assert '❌' in cancel_buttons[0].label


class TestOnTimeout:
    """Testes para on_timeout."""

    @pytest.mark.asyncio
    async def test_on_timeout_does_not_raise(self):
        """Deve executar on_timeout sem levantar exceção."""
        view = ConfirmationView()
        # Não deve levantar exceção
        await view.on_timeout()


class TestConfirmationViewState:
    """Testes de estado da ConfirmationView."""

    def test_value_none_initially(self):
        """value deve ser None inicialmente."""
        view = ConfirmationView()
        assert view.value is None

    def test_timeout_default_60_seconds(self):
        """Timeout padrão deve ser 60 segundos."""
        view = ConfirmationView()
        assert view.timeout == 60.0

    def test_timeout_can_be_customized(self):
        """Timeout pode ser customizado."""
        view = ConfirmationView(timeout=120.0)
        assert view.timeout == 120.0

    def test_view_not_finished_initially(self):
        """View não deve estar finalizada inicialmente."""
        view = ConfirmationView()
        assert not view.is_finished()

    def test_children_are_buttons(self):
        """Filhos devem ser botões Discord UI."""
        view = ConfirmationView()
        from discord.ui import Button

        for child in view.children:
            assert isinstance(child, Button)


class TestConfirmationViewBehavior:
    """Testes de comportamento da ConfirmationView."""

    def test_multiple_instances_independent(self):
        """Múltiplas instâncias devem ser independentes."""
        view1 = ConfirmationView(timeout=30.0)
        view2 = ConfirmationView(timeout=60.0)

        assert view1.timeout == 30.0
        assert view2.timeout == 60.0
        assert view1 is not view2

    def test_value_attribute_writable(self):
        """value pode ser alterado (usado pelos callbacks)."""
        view = ConfirmationView()
        assert view.value is None

        # Simular o que o callback do botão faz
        view.value = True
        assert view.value is True

        view.value = False
        assert view.value is False

    def test_clear_items_method_exists(self):
        """Método clear_items deve existir."""
        view = ConfirmationView()
        assert hasattr(view, 'clear_items')
        assert callable(view.clear_items)

    def test_stop_method_exists(self):
        """Método stop deve existir."""
        view = ConfirmationView()
        assert hasattr(view, 'stop')
        assert callable(view.stop)
