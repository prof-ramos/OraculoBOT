"""Componentes de UI do Discord (Human-in-the-Loop)."""

from __future__ import annotations

from typing import Optional

import discord
from agno.utils.log import log_warning


class ConfirmationView(discord.ui.View):
    """Botões de confirmação/cancelamento para execução de tools."""

    def __init__(self, timeout: float = 60.0) -> None:
        super().__init__(timeout=timeout)
        self.value: Optional[bool] = None

    @discord.ui.button(label="✅ Confirmar", style=discord.ButtonStyle.primary)
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.value = True
        button.disabled = True
        await interaction.response.edit_message(view=self)
        self.clear_items()
        self.stop()

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary)
    async def cancel(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.value = False
        button.disabled = True
        await interaction.response.edit_message(view=self)
        self.clear_items()
        self.stop()

    async def on_timeout(self) -> None:
        log_warning("ConfirmationView: timeout atingido")
