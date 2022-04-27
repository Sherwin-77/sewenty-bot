import discord
from discord.ext import commands
from datetime import datetime
import asyncio

# TODO: change cmdCooldown to set type
cmdCooldown = {}

EMOJI_STATUS = {
    "online": "🟢",
    "idle": "🌙",
    "dnd": "🚫",
    "offline": "⚫"
}


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='member', help='List all members nickname (doesnt work > 50)')
    async def member_name(self, ctx):
        member_count = ctx.guild.member_count
        await ctx.send(f'Total members: {member_count}')
        if member_count <= 50:
            member_name = []
            for member in ctx.guild.members:
                if member.nick is None:
                    member_name.append(str(member.name))
                else:
                    member_name.append(str(member.nick))
            member_list = '\n- '.join(member_name)
            await ctx.send(f'```Members: \n- {member_list}```')

    @commands.command(name='suggest', help='Give a suggestion')
    async def suggest(self, ctx, *suggestion):
        if suggestion:
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
        else:
            await ctx.reply('Please input your suggestion')

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
    async def find_user(self, ctx, user: discord.User = None):
        if not user:
            user = ctx.author
        yellow = 0xfff00
        await ctx.trigger_typing()
        flags = map(dirty_filter, user.public_flags.all()) if user.public_flags.value != 0 else ["None"]
        custom_embed = discord.Embed(title="User Data", description=f"Created at: "
                                                                    f"<t:{int(user.created_at.timestamp())}:R>\n"
                                                                    f"Bot: {user.bot} **|** System: {user.system}\n"
                                                                    f"Public Flags: "
                                                                    f"{', '.join(flags)}",
                                     color=yellow)
        custom_embed.set_author(name=f"{user.name}#{user.discriminator}", icon_url=user.avatar)
        member = ctx.guild.get_member(user.id)
        if member:
            boost = member.premium_since
            if not boost:
                boost = -1e+13
            else:
                boost = boost.timestamp()
            custom_embed.add_field(name="Member info",
                                   value=f"Mobile:\u1CBC\u1CBC{EMOJI_STATUS[member.mobile_status.value]}\n"
                                         f"Desktop:\u1CBC{EMOJI_STATUS[member.desktop_status.value]}\n"
                                         f"Web: \u1CBC\u1CBC\u1CBC\u1CBC{EMOJI_STATUS[member.web_status.value]}\n"
                                         f"Joined since: <t:{int(member.joined_at.timestamp())}:R>\n"
                                         f"Boosting since: <t:{int(boost)}:R>\n"
                                         f"Nick: {member.nick}",
                                   inline=False)   # no spaces? fine I'll do it myself
        await ctx.send(embed=custom_embed)

    @commands.command(name="avatar", help="yes avatar")
    async def show_avatar(self, ctx, user: discord.User = None):
        if ctx.author.id in cmdCooldown:
            return
        if not user:
            user = ctx.author
        embed = discord.Embed(title='Avatar')
        embed.set_author(name=user.name, icon_url=user.avatar)
        embed.set_image(url=user.avatar)
        await ctx.send(embed=embed)
        cmdCooldown.update({str(ctx.author.id): True})
        await asyncio.sleep(3)
        cmdCooldown.pop(str(ctx.author.id))

    @commands.command(name="avatar2")
    async def show_avatar2(self, ctx, user: discord.Member = None):
        """
        Avatar V2!! with ~~useless~~ updated feature
        """
        if ctx.author.id in cmdCooldown:
            return
        if not user:
            user = ctx.author
        embed = discord.Embed(title='Avatar')
        embed.set_author(name=user.display_name, icon_url=user.display_icon)
        embed.set_image(url=user.guild_avatar)
        await ctx.send(embed=embed)
        cmdCooldown.update({str(ctx.author.id): True})
        await asyncio.sleep(3)
        cmdCooldown.pop(str(ctx.author.id))

    @commands.command(name="banner", help="beta")
    async def check_banner(self, ctx, user: discord.User = None):
        """
        Returns a user's Discord banner
        """
        # PENDING: below code only execute in 2.0 which waiting to be released
        if not user:
            user = ctx.author
        member = await self.bot.fetch_user(user.id)
        banner_url = member.banner
        if not banner_url:
            banner_url = "https://c4.wallpaperflare.com/wallpaper/" \
                         "357/645/211/easter-island-chile-starry-night-statue-wallpaper-preview.jpg"

        custom_embed = discord.Embed(description=f"{member.name}'s banner")
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

    @commands.command(name='invite', help="Invite this bot to your server")
    async def link(self, ctx):
        await ctx.send(
            'https://discord.com/api/oauth2/'
            'authorize?client_id=719051490257272842&permissions=388160&scope=bot%20applications.commands',
            delete_after=30)


def dirty_filter(text):
    """
    Function to filter dot underscore in PublicFlag and title them

    Args:
        text (Any): text to filter

    Returns:
        str: Filtered text

    """
    return text.name.split('.')[-1].replace('_', ' ').title()


async def setup(bot):
    await bot.add_cog(General(bot))
