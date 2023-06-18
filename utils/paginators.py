import discord
from discord.ext import menus

from typing import Callable


class SimplePages(discord.ui.View, menus.MenuPages):
    """Pagination with ui button"""
    def __init__(self, source: menus.PageSource, *, delete_message_after=True):
        super().__init__(timeout=60)
        self._source = source
        self.current_page = 0
        self.ctx = None
        self.message = None
        self.delete_message_after = delete_message_after

    async def start(self, ctx, *, channel=None, wait=False):
        await self._source._prepare_once()
        self.ctx = ctx
        self.message = await self.send_initial_message(ctx, ctx.channel)

    async def _get_kwargs_from_page(self, page):
        value = await super()._get_kwargs_from_page(page)
        if "view" not in value:
            value.update({"view": self})
        return value

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user == self.ctx.author

    @discord.ui.button(emoji='⏪', style=discord.ButtonStyle.blurple)
    async def skip_to_first(self, interaction, _):
        await self.show_page(0)
        await interaction.response.edit_message(view=self)

    @discord.ui.button(emoji='◀', style=discord.ButtonStyle.blurple)
    async def back_page(self, interaction, _):
        await self.show_checked_page(self.current_page-1)
        await interaction.response.edit_message(view=self)

    @discord.ui.button(emoji='⏹', style=discord.ButtonStyle.blurple)
    async def stop_page(self, interaction, _):
        for child in self.children:
            child.disabled = True
        self.stop()
        if self.delete_message_after:
            await self.message.delete()
        else:
            await self.show_current_page()
        await interaction.response.edit_message(view=self)

    @discord.ui.button(emoji='▶', style=discord.ButtonStyle.blurple)
    async def next_page(self, interaction, _):
        await self.show_checked_page(self.current_page+1)
        await interaction.response.edit_message(view=self)

    @discord.ui.button(emoji='⏩', style=discord.ButtonStyle.blurple)
    async def skip_to_last(self, interaction, _):
        await self.show_page(self._source.get_max_pages()-1)
        await interaction.response.edit_message(view=self)


# https://github.com/Rapptz/discord-ext-menus#pagination
class EmbedSource(menus.ListPageSource):
    def __init__(self, entries, per_page=4, title=None):
        super().__init__(entries, per_page=per_page)
        self.title = title

    async def format_page(self, menu: menus, page, description_setter: Callable = None):
        offset = menu.current_page * self.per_page  # type: ignore
        embed = discord.Embed(color=discord.Colour.random())
        embed.description = '\n'.join(f"{i+1}. {v}" for i, v in enumerate(page, start=offset))
        if self.title is not None:
            embed.title = self.title
        if description_setter is not None:
            embed.description = description_setter(page)
        return embed
