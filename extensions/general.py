from __future__ import annotations

import discord
from discord.ext import commands
from datetime import datetime

from os import getenv
from typing import TYPE_CHECKING, Optional, Union

from constants import EMOJI_STATUS

if TYPE_CHECKING:
    from main import SewentyBot


# noinspection SpellCheckingInspection
class General(commands.Cog):
    def __init__(self, bot: SewentyBot):
        self.bot: SewentyBot = bot

        self.DEFAULT_BANNER_URL = getenv("DEFAULT_BANNER_URL")
    #     self._cd = commands.CooldownMapping.from_cooldown(rate=1.0, per=3.0, type=commands.BucketType.user)
    #
    # async def cog_check(self, ctx):
    #     bucket = self._cd.get_bucket(ctx.message)
    #     retry_after = bucket.update_rate_limit()
    #     if retry_after:
    #         raise commands.CommandOnCooldown(bucket, retry_after, commands.BucketType.user)
    #     return True

    @commands.command(help="Give a suggestion")
    async def suggest(self, ctx, *, suggestion):
        blue = 0x00ffff
        channel = self.bot.get_channel(759728217069191209)
        username = await self.bot.fetch_user(ctx.author.id)
        custom_embed = discord.Embed(title=f"{username}\'s Suggestion", description=suggestion, color=blue)
        await channel.send(embed=custom_embed)
        await ctx.message.add_reaction('👍')

    @suggest.error
    async def suggest_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.reply("Please input your suggestion :c", mention_author=False, delete_after=5)

    @commands.command()
    async def ping(self, ctx):
        time0 = discord.utils.snowflake_time(ctx.message.id).replace(tzinfo=None)
        ping = round(self.bot.latency * 1000)
        time1 = datetime.utcnow().replace(tzinfo=None)
        message = await ctx.reply(f':ping_pong: Pong! in: {ping} ms', mention_author=False)
        message_id = message.id
        time_diff1 = round((time1 - time0).microseconds / 1000)
        time_diff2 = round((discord.utils.snowflake_time(message_id).replace(tzinfo=None) - time1).microseconds / 1000)
        await message.edit(
            content=f':ping_pong: Pong! in: {ping} ms\nMessage received in: {time_diff1} ms\n'
                    f'Message sent in: {time_diff2} ms', allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    async def whois(self, ctx: commands.Context, user: Optional[discord.User] = None):
        if not user:
            user = ctx.author
        async with ctx.typing():
            flags = map(dirty_filter, user.public_flags.all()) if user.public_flags.value != 0 else ["None"]
            custom_embed = discord.Embed(title="User Data", description=f"Created at: "
                                                                        f"<t:{int(user.created_at.timestamp())}:D>\n"
                                                                        f"Bot: **{user.bot}**\n"
                                                                        f"System: **{user.system}**\n"
                                                                        f"Public Flags: "
                                                                        f"**{', '.join(flags)}**",
                                         color=user.accent_color or discord.Colour.random())
            custom_embed.set_author(name=str(user), icon_url=user.avatar)
            custom_embed.set_footer(text=user.id)
            member = ctx.guild.get_member(user.id)
            if member:
                member: discord.Member
                boost = member.premium_since
                if not boost:
                    boost = discord.utils.utcnow()
                    boost = discord.utils.format_dt(boost.replace(year=boost.year-69), style='R')
                    boost += " ||Not boosting||"
                else:
                    boost = discord.utils.format_dt(boost, style='R')
                custom_embed.add_field(name="Member info",
                                       value=f"Top Role: {member.top_role.mention}\n"
                                             f"Mobile:\u2800\u2800 {EMOJI_STATUS[str(member.mobile_status)]}\n"
                                             f"Desktop:\u2800 {EMOJI_STATUS[str(member.desktop_status)]}\n"
                                             f"Web:\u2800\u2800\u2800 {EMOJI_STATUS[str(member.web_status)]}\n"
                                             f"Pending verification: **{member.pending}**\n"
                                             f"Joined at: {discord.utils.format_dt(member.joined_at)}\n"
                                             f"Boosting since: {boost}\n"
                                             f"Nick: {member.nick}",
                                       inline=False)   # no spaces? fine I'll do it myself
                custom_embed.add_field(name="< - - - Permissions - - - >",
                                       value=', '.join([perm.replace('_', ' ').capitalize()
                                                        for perm, value in iter(member.guild_permissions)
                                                        if value]),
                                       inline=False)
                if member.display_icon:
                    custom_embed.set_author(name=str(user), icon_url=member.display_icon)
                    custom_embed.set_thumbnail(url=member.display_avatar)
            await ctx.send(embed=custom_embed)

    @commands.command(aliases=["av"])
    async def avatar(self, ctx, user: Optional[Union[discord.Member, discord.User]] = None):
        """
        Just avatar
        """
        if not user:
            user = ctx.author
        embed = discord.Embed(title="Avatar", color=user.accent_color or discord.Colour.random())
        embed.set_author(name=user.display_name, icon_url=user.avatar)
        embed.set_image(url=user.display_avatar)
        await ctx.send(embed=embed)

    @commands.command(aliases=['b'])
    async def banner(self, ctx, user: Optional[discord.User] = None):
        """
        Returns a user's Discord banner
        """
        if not user:
            user = ctx.author
        user = await self.bot.fetch_user(user.id)
        banner_url = user.banner or self.DEFAULT_BANNER_URL
        custom_embed = discord.Embed()
        custom_embed.set_author(name=f"{user.display_name}'s banner", icon_url=user.display_avatar)
        custom_embed.set_image(url=banner_url)
        await ctx.send(embed=custom_embed)
        # if not user:
        #     user = ctx.author
        # member = await ctx.guild.fetch_member(user.id)
        # req = await self.bot.http.request(discord.http.Route("GET", "/users/{uid}", uid=user.id))
        # banner_id = req["banner"]
        # ext = "png"
        # if banner_id and banner_id.startswith("a_"):
        #     ext = "gif"
        # # If statement because the user may not have a banner
        # if not banner_id:
        #     await ctx.send("User doesn't have banner", delete_after=5)
        #     return
        # banner_url = f"https://cdn.discordapp.com/banners/{user.id}/{banner_id}.{ext}?size=1024"
        # custom_embed = discord.Embed(title="Banner", color=member.colour)
        # custom_embed.set_author(name=user.name)
        # custom_embed.set_image(url=banner_url)
        # await ctx.send(embed=custom_embed)

    @commands.command(aliases=["gb"])
    async def gbanner(self, ctx):
        """
        Returns guild banner if exist
        """
        banner_url = ctx.guild.banner or self.DEFAULT_BANNER_URL
        custom_embed = discord.Embed(color=discord.Colour.random())
        custom_embed.set_author(name="Server banner", icon_url=ctx.guild.icon)
        custom_embed.set_image(url=banner_url)
        await ctx.send(embed=custom_embed)


def dirty_filter(text):
    """
    Function to filter dot underscore in PublicFlag and title them

    Args:
        text (Any): text to filter

    Returns:
        str: Filtered text

    """
    return text.name.split('.')[-1].replace('_', ' ').title()


async def setup(bot: SewentyBot):
    await bot.add_cog(General(bot))
