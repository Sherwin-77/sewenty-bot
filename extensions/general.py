from __future__ import annotations

import discord
from discord.ext import commands
from datetime import datetime

from os import getenv
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from main import SewentyBot


class General(commands.Cog):
    def __init__(self, bot: SewentyBot):
        self.bot: SewentyBot = bot
        self.EMOJI_STATUS = {
            "online": "🟢",
            "idle": "🌙",
            "dnd": "🚫",
            "offline": "⚫"
        }

        self.DEFAULT_BANNER_URL = getenv("DEFAULT_BANNER_URL")
    #     self._cd = commands.CooldownMapping.from_cooldown(rate=1.0, per=3.0, type=commands.BucketType.user)
    #
    # async def cog_check(self, ctx):
    #     bucket = self._cd.get_bucket(ctx.message)
    #     retry_after = bucket.update_rate_limit()
    #     if retry_after:
    #         raise commands.CommandOnCooldown(bucket, retry_after, commands.BucketType.user)
    #     return True

    @commands.command(name='suggest', help='Give a suggestion')
    async def suggest(self, ctx, *, suggestion):
        blue = 0x00ffff
        msg = []
        for x in suggestion:
            msg.append(x)
        channel = self.bot.get_channel(759728217069191209)
        messages = ' '.join(msg)
        username = await self.bot.fetch_user(ctx.author.id)
        custom_embed = discord.Embed(title=f'{username}\'s Suggestion', description=messages, color=blue)
        await channel.send(embed=custom_embed)
        await ctx.message.add_reaction('👍')

    @suggest.error
    async def suggest_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.reply("Please input your suggestion :c", mention_author=False, delete_after=5)

    @commands.command(name='ping')
    async def pinging(self, ctx):
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

    @commands.command(name='whois')
    async def find_user(self, ctx: commands.Context, user: Optional[discord.User] = None):
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
                    boost = -1e+13
                else:
                    boost = boost.timestamp()
                custom_embed.add_field(name="Member info",
                                       value=f"Top Role: {member.top_role.mention}\n"
                                             f"Mobile:\u2800\u2800 {self.EMOJI_STATUS[str(member.mobile_status)]}\n"
                                             f"Desktop:\u2800 {self.EMOJI_STATUS[str(member.desktop_status)]}\n"
                                             f"Web:\u2800\u2800\u2800 {self.EMOJI_STATUS[str(member.web_status)]}\n"
                                             f"Pending verification: **{member.pending}**\n"
                                             f"Joined at: <t:{int(member.joined_at.timestamp())}:D>\n"
                                             f"Boosting since: <t:{int(boost)}:R>\n"
                                             f"Nick: {member.nick}",
                                       inline=False)   # no spaces? fine I'll do it myself
                if member.display_icon:
                    custom_embed.set_author(name=str(user), icon_url=member.display_icon)
                    custom_embed.set_thumbnail(url=member.display_avatar)
            await ctx.send(embed=custom_embed)

    @commands.command(name="avatar", help="yes avatar", aliases=["av"])
    async def show_avatar(self, ctx, user: Optional[discord.User] = None):
        if not user:
            user = ctx.author
        embed = discord.Embed(title='Avatar')
        embed.set_author(name=user.name, icon_url=user.avatar)
        embed.set_image(url=user.avatar)
        await ctx.send(embed=embed)

    @commands.command(name="avatar2", aliases=["av2"])
    async def show_avatar2(self, ctx, user: Optional[discord.Member] = None):
        """
        Avatar V2!! with ~~useless~~ updated feature
        """
        if not user:
            user = ctx.author
        embed = discord.Embed(title='Avatar')
        embed.set_author(name=user.display_name, icon_url=user.display_icon)
        embed.set_image(url=user.guild_avatar)
        await ctx.send(embed=embed)

    @commands.command(name="banner")
    async def check_banner(self, ctx, user: Optional[discord.User] = None):
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
