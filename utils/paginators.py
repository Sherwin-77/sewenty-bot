import discord
from discord.ext import menus


class SimplePages(discord.ui.View, menus.MenuPages):
    """Pagination with ui button"""
    def __init__(self, source: menus.PageSource, *, delete_message_after=False):
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
    async def skip_to_first(self, button, interaction):
        await self.show_page(0)

    @discord.ui.button(emoji='◀', style=discord.ButtonStyle.blurple)
    async def back_page(self, button, interaction):
        await self.show_checked_page(self.current_page-1)

    @discord.ui.button(emoji='⏹', style=discord.ButtonStyle.blurple)
    async def stop_page(self, button, interaction):
        self.stop()
        if self.delete_message_after:
            await self.message.delete()

    @discord.ui.button(emoji='⏹', style=discord.ButtonStyle.blurple)
    async def next_page(self, button, interaction):
        await self.show_checked_page(self.current_page+1)

    @discord.ui.button(emoji='⏩', style=discord.ButtonStyle.blurple)
    async def skip_to_last(self, button, interaction):
        await self.show_page(self._source.get_max_pages()-1)


class InteractionBasedSource(menus.ListPageSource):
    """ListPageSource with interaction support"""
    def __init__(self, button, entries, **options):
        super().__init__(entries, **options)
        self.button = button

    async def format_page(self, menu, page):
        raise NotImplementedError

