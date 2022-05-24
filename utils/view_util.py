import discord

from typing import List


class ConfirmEmbed(discord.ui.View):
    def __init__(self, message):
        super().__init__()
        self.value = None
        self.embed = discord.Embed(title="Confirmation!",
                                   description=message,
                                   color=discord.Colour.random())

    @discord.ui.button(emoji='✅', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, __: discord.Button):
        self.value = True
        await interaction.response.edit_message(content="Success", view=None, embed=None)
        self.stop()

    @discord.ui.button(emoji='❎', style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, __: discord.Button):
        self.value = False
        await interaction.response.edit_message(content="Operation cancelled", view=None, embed=None)
        self.stop()


class Dropdown(discord.ui.Select):
    def __init__(self, text: str, select_list: List[discord.SelectOption]):
        super().__init__(placeholder=text, min_values=1, max_values=1, options=select_list)

    async def callback(self, interaction: discord.Interaction):
        raise NotImplementedError
