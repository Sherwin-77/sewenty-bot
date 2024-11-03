from __future__ import annotations

import discord
from discord.ext import commands

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from main import SewentyBot


class Action(commands.GroupCog, group_name="action"):
    def __init__(self, bot: SewentyBot):
        self.bot: SewentyBot = bot
        self.action_collection = self.bot.DB["action"]
        self._cd = commands.CooldownMapping.from_cooldown(rate=1.0, per=3.0, type=commands.BucketType.user)

    async def cog_check(self, ctx):
        if ctx.invoked_with is not None and ctx.invoked_with == "help":
            return True
        bucket = self._cd.get_bucket(ctx.message)
        if bucket is None:
            return
        retry_after = bucket.update_rate_limit()
        if retry_after:
            raise commands.CommandOnCooldown(bucket, retry_after, commands.BucketType.user)
        return True

    @staticmethod
    async def query_member(ctx: commands.Context, user) -> Optional[discord.Member]:
        ret = None
        try:
            ret = await commands.MemberConverter().convert(ctx, user)
        except commands.errors.MemberNotFound:
            user = user.lower()

        if ret is None and ctx.guild is not None:
            for member in ctx.guild.members:
                if user in member.name.lower() or (member.nick is not None and user in member.nick.lower()):
                    if ret is None or ret.id > member.id:
                        ret = member
        return ret

    async def update_action(self, ctx: commands.Context, userid: str, action: str) -> int:
        users = {}
        counts = 1
        query = {"_id": f"{ctx.author.id}{action}"}
        cursor = await self.action_collection.find_one(query)
        if cursor:
            users = cursor["users"]
        if userid in users:
            counts += users[userid]
        users.update({userid: counts})

        if not cursor:
            await self.action_collection.insert_one({"_id": f"{ctx.author.id}{action}", "users": users})
        else:
            await self.action_collection.update_one(query, {"$set": {"users": users}})
        return counts

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if (
            not message.content.lower().startswith('y')
            or self.bot.TEST_MODE
            and message.guild is not None
            and message.guild.id != 714152739252338749
        ):
            return
        offset = 1
        if message.content.lower().startswith("yui"):
            offset += 2
        clean_prefix = message.content[offset:]
        command = clean_prefix.strip().split(' ')[0].lower()
        command_list = {c.name for c in self.get_commands()}
        if command not in command_list:
            return
        prefix = await self.bot.get_prefix(message)
        message.content = prefix[0] + clean_prefix
        await self.bot.process_commands(message)

    @commands.command()
    async def shifu(self, ctx, *, user):
        """
        No ping
        """
        target = await self.query_member(ctx, user)

        if target is None:
            return await ctx.send("User ded")

        await ctx.send(f"You shifued {target.mention}!", allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    async def haki(self, ctx, *, user):
        """
        Has ping
        """
        target = await self.query_member(ctx, user)

        if target is None:
            return await ctx.send("User ded")

        await ctx.send(f"You hakied {target.mention}! <:hikanopls:804522598289375232>")

    @commands.command()
    async def meo(self, ctx, *, user):
        """
        Meow
        """
        target = await self.query_member(ctx, user)

        if target is None:
            return await ctx.send("User ded")

        await ctx.send(f"You meo-ed {target.mention}! <a:catMIAOwO:782034693905186816>")

    @commands.command()
    async def flake(self, ctx, *, user):
        """
        No ping
        """
        target = await self.query_member(ctx, user)

        if target is None:
            return await ctx.send("User ded")

        await ctx.send(f"You flaked {target.mention}!", allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    async def broom(self, ctx, *, user):
        """
        Broom
        """
        target = await self.query_member(ctx, user)

        if target is None:
            return await ctx.send("User ded")

        await ctx.send(f"You broomed {target.mention}! 🧹", allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    async def sleep(self, ctx, *, user: Optional[str] = None):
        """Sleep with someone"""
        if user is None:
            return await ctx.send(
                f"{ctx.author.mention} sleep peacefully (maybe) today...", allowed_mentions=discord.AllowedMentions.none()
            )
        target = await self.query_member(ctx, user)
        if target is None:
            return await ctx.send("User ded")
        if target.id == ctx.author.id:
            return await ctx.send(
                f"{ctx.author.mention} sleep peacefully (maybe) today...", allowed_mentions=discord.AllowedMentions.none()
            )

        counts = await self.update_action(ctx, str(target.id), "sleep")
        await ctx.send(
            f"{ctx.author.mention} sleeps with {target.mention}...\n" f"That's {counts} sleeps now~",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.command()
    async def hug(self, ctx, *, user):
        """Hug"""
        target = await self.query_member(ctx, user)
        if target is None:
            return await ctx.send("User ded")
        if target.id == ctx.author.id:
            return await ctx.send("It's okay I'll hug you... ;-;")
        
        counts = await self.update_action(ctx, str(target.id), "hug")
        custom_embed = discord.Embed(
            title="You gave a hug!",
            description=f"{ctx.author.mention} hugs {target.mention}",
            url="https://discord.com/api/oauth2/authorize?client_id=719051490257272842"
            "&permissions=412384349248&scope=bot%20applications.commands",
            color=discord.Colour.random(),
        )
        custom_embed.set_footer(text=f"Thats {counts} hugs now!")
        await ctx.send(embed=custom_embed)

    @commands.command()
    async def pat(self, ctx, *, user):
        """Pat pat"""
        target = await self.query_member(ctx, user)
        if target is None:
            return await ctx.send("User ded")
        if target.id == ctx.author.id:
            return await ctx.send("aww :c I'll pat you instead...")

        counts = await self.update_action(ctx, str(target.id), "pat")
        await ctx.send(
            f"{ctx.author.mention} pats {target.mention}.\n" f"That's {counts} pats now!",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.command()
    async def bite(self, ctx, *, user):
        """bite"""
        target = await self.query_member(ctx, user)
        if target is None:
            return await ctx.send("User ded")
        if target.id == ctx.author.id:
            return await ctx.send("Nu bite self :c")

        counts = await self.update_action(ctx, str(target.id), "bite")
        custom_embed = discord.Embed(
            title="You gave a bite!",
            description=f"{ctx.author.mention} bites {target.mention}",
            url="https://discord.com/api/oauth2/authorize?client_id=719051490257272842"
            "&permissions=412384349248&scope=bot%20applications.commands",
            color=discord.Colour.random(),
        )
        custom_embed.set_footer(text=f"That's {counts} bites now!")
        await ctx.send(embed=custom_embed)

    @commands.command()
    async def cuddle(self, ctx, *, user):
        """cuddle"""
        target = await self.query_member(ctx, user)
        if target is None:
            return await ctx.send("User ded")
        if target.id == ctx.author.id:
            return await ctx.send("Do you need some cuddle :c")

        counts = await self.update_action(ctx, str(target.id), "cuddle")
        custom_embed = discord.Embed(
            title="You gave a cuddle!",
            description=f"{ctx.author.mention} cuddles {target.mention}",
            url="https://discord.com/api/oauth2/authorize?client_id=719051490257272842"
            "&permissions=412384349248&scope=bot%20applications.commands",
            color=discord.Colour.random(),
        )
        custom_embed.set_footer(text=f"That's {counts} cuddles now!")
        await ctx.send(embed=custom_embed)

    @commands.command()
    async def cookie(self, ctx, *, user):
        """Cookie"""
        target = await self.query_member(ctx, user)
        if target is None:
            return await ctx.send("User ded")
        if target.id == ctx.author.id:
            return await ctx.send("No >:(")

        counts = await self.update_action(ctx, str(target.id), "cookie")
        await ctx.send(
            f"{ctx.author.mention} gave {target.mention} a cookie!\n" f"That's {counts} cookies now!",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.command()
    async def counters(self, ctx: commands.Context, action: str, *, user: Optional[str] = None):
        action = action.lower()
        if action.endswith('s'):
            action = action.removesuffix('s')
        target = ctx.author
        if ctx.guild is None:
            return
        if user is not None:
            target = await self.query_member(ctx, user)
        if target is None:
            return await ctx.send("Unable to find user")
        query = {"_id": f"{target.id}{action}"}
        cursor = await self.action_collection.find_one(query)
        if not cursor:
            return await ctx.send("Not found")
        top = dict(sorted(cursor["users"].items(), key=lambda it: it[1], reverse=True))
        res = ""
        i = 1
        total = 0
        res += '┌' + ('─' * 26) + '┬' + ('─' * 8) + "┐\n"
        res += "│ Member " + (' ' * 18) + "│ Count  │\n"
        res += '├' + ('─' * 26) + '┼' + ('─' * 8) + "┤\n"
        for userid, counts in top.items():
            if i > 25 and len(top) > 25:
                total += counts
                continue
            member = ctx.guild.get_member(int(userid))
            display = f"User-{userid}"
            if member is not None:
                display = member.display_name
            if len(display) > 24:
                res += f"│ {display[:24]:<24} │ {counts:<6} │\n"
                res += f"│ {display[24:]:<24} │ {' ' * 6} │\n"
            else:
                res += f"│ {display:<24} │ {counts:<6} │\n"
            i += 1
        res += '└' + ('─' * 26) + '┴' + ('─' * 8) + "┘\n"
        if total > 0:
            res += f"And {total} more {action}s to {len(top)-25}"
        custom_embed = discord.Embed(
            description=f"This leaderboard is for given {action}s\n" f"```\n" f"{res}\n" f"```", color=discord.Colour.green()
        )
        custom_embed.set_author(
            name=f"{target.display_name}'s leaderboard", icon_url=target.avatar.url if target.avatar else None
        )
        await ctx.send(embed=custom_embed)


async def setup(bot: SewentyBot):
    await bot.add_cog(Action(bot))
