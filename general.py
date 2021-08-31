import discord
from discord.ext import commands
from datetime import datetime
import asyncio
owoCooldown = {}


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

    @commands.command(name='clear', help='Clear the message. Ex: clear 20 (max 100)', aliases=['purge', 'delete'])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, number=5):
        mgs = []
        number = int(number)
        async for x in ctx.message.channel.history(limit=number):
            mgs.append(x)
        await ctx.channel.delete_messages(mgs)
        await ctx.send(f'Deleted {number} Messages 🧹')

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
        time_diff2 = round((discord.utils.snowflake_time(message_id) - time1).microseconds / 1000)
        await message.edit(
            content=f':ping_pong: Pong! in: {ping} ms\nMessage received in: {time_diff1} ms\n'
                    f'Message sent in: {time_diff2} ms', allowed_mentions=discord.AllowedMentions.none())

    @commands.command(name='whois')
    async def find_user(self, ctx, user: discord.User):
        yellow = 0xfff00
        username = user.name
        user_tag = user.discriminator
        user_date = user.created_at
        user_bot = user.bot
        await ctx.trigger_typing()
        custom_embed = discord.Embed(title='User Data', description=f'Created at: {user_date}\n'
                                                                    f'Bot: {user_bot}', color=yellow)
        custom_embed.set_author(name=f"{username}#{user_tag}", icon_url=user.avatar_url)
        await ctx.send(embed=custom_embed)

    @commands.command(name='avatar', help='yes avatar')
    async def avaa(self, ctx, userid=None):
        if ctx.author.id in owoCooldown:
            return
        if not userid:
            embed = discord.Embed(title='Avatar')
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            embed.set_image(url=ctx.author.avatar_url)
            await ctx.send(embed=embed)
            owoCooldown.update({str(ctx.author.id): True})
            await asyncio.sleep(3)
            owoCooldown.pop(str(ctx.author.id))

        else:
            userid = int((((userid.replace('<', '')).replace('>', '')).replace('@', '')).replace('!', ''))
            embed = discord.Embed(title='Avatar')
            username = await self.bot.fetch_user(userid)
            embed.set_author(name=username.name, icon_url=username.avatar_url)
            embed.set_image(url=username.avatar_url)
            await ctx.send(embed=embed)
            owoCooldown.update({str(ctx.author.id): True})
            await asyncio.sleep(3)
            owoCooldown.pop(str(ctx.author.id))

    @commands.command(name="banner", help="beta")
    async def check_banner(self, ctx, user: discord.User = None):
        if not user:
            user = ctx.author
        member = await ctx.guild.fetch_member(user.id)
        req = await self.bot.http.request(discord.http.Route("GET", "/users/{uid}", uid=user.id))
        banner_id = req["banner"]
        ext = "png"
        if banner_id and banner_id.startswith("a_"):
            ext = "gif"
        # If statement because the user may not have a banner
        if not banner_id:
            await ctx.send("User doesn't have banner", delete_after=5)
            return
        banner_url = f"https://cdn.discordapp.com/banners/{user.id}/{banner_id}.{ext}?size=1024"
        custom_embed = discord.Embed(title="Banner", color=member.colour)
        custom_embed.set_author(name=user.name, icon_url=user.avatar_url)
        custom_embed.set_image(url=banner_url)
        await ctx.send(embed=custom_embed)

    @commands.command(name='invite', help="Invite this bot to your server")
    async def link(self, ctx):
        await ctx.send(
            'https://discord.com/api/oauth2/'
            'authorize?client_id=719051490257272842&permissions=388160&scope=bot%20applications.commands',
            delete_after=30)


def setup(bot):
    bot.add_cog(General(bot))