from __future__ import annotations
from typing import TYPE_CHECKING, List

from copy import deepcopy
import datetime
import logging

import discord
from discord.ext import commands, tasks

from utils import paginators
from utils.view_util import Dropdown

if TYPE_CHECKING:
    from main import SewentyBot

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s:%(name)s: %(message)s")
logger = logging.getLogger("extension.lovesick")


class SelectDropdown(Dropdown):
    def __init__(self, text: str, select_list: List[discord.SelectOption], recruit_log):
        self.recruit_log = recruit_log
        super().__init__(text, select_list)

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        if interaction.user.id != self.view.ctx.author.id:
            return await interaction.response.send_message("You are not allowed to do this :c", ephemeral=True)
        await self.view.change_source(paginators.EmbedSource(self.recruit_log[self.values[0]] or ["None here"], 10))
        for x in self.options:
            if x.value == self.values[0]:
                x.default = True
            else:
                x.default = False
        await interaction.response.edit_message(view=self.view)


class LoveSick(commands.Cog):
    GUILD_ID = 714152739252338749

    def __init__(self, bot: SewentyBot):
        self.bot: SewentyBot = bot
        self.refresh_lxv_recruit.start()
        self.LXV_COLLECTION = self.bot.DB["lovesick"]
        self.BLUEPRINT = {
            "added": [],
            "expired": [],
            "deleted": []
        }

        self.logging_channel_id = 789154199186702408
        self.lxv_recruit_id = 769135734086959104
        self.mod_ids = {714165505153302639, 714165560853790741, 714197482699227265}
        self.counter = -1
        self.last_checked = None
        self.recruit_log = deepcopy(self.BLUEPRINT)

    def cog_check(self, ctx) -> bool:
        return ctx.guild.id == self.GUILD_ID

    async def cog_unload(self) -> None:
        self.refresh_lxv_recruit.cancel()

    @tasks.loop(hours=12)
    async def refresh_lxv_recruit(self):
        guild = self.bot.get_guild(self.GUILD_ID)
        role = guild.get_role(self.lxv_recruit_id)
        channel = guild.get_channel(self.logging_channel_id)
        if role is None:
            if channel is None:
                return await self.bot.send_owner(f"General channel for lxv is missing. Old: {self.logging_channel_id}\n"
                                                 f"LXV recruit role missing. Old: {self.lxv_recruit_id}")
            else:
                await channel.send(f"LXV recruit role missing. Old id: {self.lxv_recruit_id}")
                return await self.bot.send_owner(f"LXV recruit role missing. Old: {self.lxv_recruit_id}")

        current_date = datetime.datetime.utcnow()
        count = await self.LXV_COLLECTION.count_documents({"_id": "lxvrecruit"})
        old_data = await self.LXV_COLLECTION.find_one({"_id": "lxvrecruit"})

        if not count:
            old_data = dict()
        else:
            old_data = old_data["members"]
        data = dict()
        self.recruit_log = deepcopy(self.BLUEPRINT)
        for member in role.members:
            member_id = f"user{member.id}"
            if member_id not in old_data:
                self.recruit_log["added"].append(f"New recruit detected: {member} ({member.id})")
                data.update({member_id: current_date})
                continue
            if member_id in old_data and (current_date - old_data[member_id]).days > 33:
                self.recruit_log["expired"].append(f"{member} ({member.id})\n "
                                                   f"From {old_data[member_id].strftime('%Y/%m/%d')} "
                                                   f"(**{(current_date - old_data[member_id]).days}** days)")
            data.update({member_id: old_data[member_id]})

        self.recruit_log["deleted"] = [f"Deleted recruit role id: {x}" for x in old_data if x not in data]
        self.last_checked = current_date

        if not count:
            await self.LXV_COLLECTION.insert_one({"_id": "lxvrecruit", "members": data})
        else:
            await self.LXV_COLLECTION.update_one({"_id": "lxvrecruit"}, {"$set": {"members": data}})
        self.counter += 1
        if not self.counter % 2:
            if channel is None:
                return await self.bot.send_owner(f"Logging channel for lxv is missing. Old: {self.logging_channel_id}")
            await channel.send("Updated lxv recruit")
        if self.recruit_log["expired"]:
            await channel.send("There are members failed to recruit. Check it from s!recruitlog")
        ch = guild.get_channel(765818685922213948)
        await ch.send("Update data completed")

    @refresh_lxv_recruit.before_loop
    async def check_connected(self):
        logger.info("Waiting for bot...")
        await self.bot.wait_until_ready()

    @commands.command(aliases=["lxvlr"])
    async def listrecruit(self, ctx):
        """
        Show list of all recruits
        """
        guild = self.bot.get_guild(self.GUILD_ID)
        role = guild.get_role(self.lxv_recruit_id)
        list_member = [f"{member.display_name} ({member.id})" for member in role.members]
        pages = paginators.SimplePages(source=paginators.EmbedSource(list_member, 10))
        await pages.start(ctx)

    @commands.command(aliases=["lxvrl"])
    async def recruitlog(self, ctx):
        """
        Core command of shidu
        added roles show a list of added recruits in past 12 hours
        deleted roles show a list of deleted recruits in past 12 hours
        expired roles show a list of recruits that exceed 30 days
        """
        dropdown = SelectDropdown(text="Select log type",
                                  select_list=[discord.SelectOption(label=key, value=value) for value, key in
                                               {
                                                   "added": "Added role",
                                                   "expired": "Expired role",
                                                   "deleted": "Deleted role"
                                               }.items()],
                                  recruit_log=self.recruit_log)
        dropdown.options[1].default = True
        pages = paginators.SimplePages(source=paginators.EmbedSource(self.recruit_log["expired"] or ["None here"], 10))
        pages.add_item(dropdown)
        await pages.start(ctx)

    @commands.command(aliases=["lxvfr"])
    async def forcerefresh(self, ctx: commands.Context):
        """
        Forcefully refreshes recruit list
        """
        if self.bot.owner != ctx.author:
            allowed = False
            for x in ctx.author.roles:
                if x.id in self.mod_ids:
                    allowed = True
                    break
            if not allowed:
                return await ctx.send("You are not allowed to use this command >:(")
        role = ctx.guild.get_role(self.lxv_recruit_id)
        current_date = datetime.datetime.utcnow()
        count = await self.LXV_COLLECTION.count_documents({"_id": "lxvrecruit"})
        old_data = await self.LXV_COLLECTION.find_one({"_id": "lxvrecruit"})

        if not count:
            old_data = dict()
        else:
            old_data = old_data["members"]
        data = dict()
        self.recruit_log = deepcopy(self.BLUEPRINT)
        for member in role.members:
            member_id = f"user{member.id}"
            if member_id not in old_data:
                self.recruit_log["added"].append(f"New recruit detected: {member} ({member.id})")
                data.update({member_id: current_date})
                continue
            if member_id in old_data and (current_date - old_data[member_id]).days > 33:
                self.recruit_log["expired"].append(f"{member} ({member.id})\n "
                                                   f"From {old_data[member_id].strftime('%Y/%m/%d')} "
                                                   f"(**{(current_date - old_data[member_id]).days}** days)")
            data.update({member_id: old_data[member_id]})

        self.recruit_log["deleted"] = [f"Deleted recruit role id: {x}" for x in old_data if x not in data]
        self.last_checked = current_date

        if not count:
            await self.LXV_COLLECTION.insert_one({"_id": "lxvrecruit", "members": data})
        else:
            await self.LXV_COLLECTION.update_one({"_id": "lxvrecruit"}, {"$set": {"members": data}})
        self.counter += 1
        await ctx.send("Successfully force refreshed")

    @commands.command()
    async def lxv(self, ctx):
        custom_embed = discord.Embed(title="This looks cool",
                                     description=f"Total update: {self.counter+1}\n"
                                                 f"Last updated: {self.last_checked}\n",
                                     color=discord.Colour.random())
        await ctx.send(embed=custom_embed)

    @commands.command(aliases=["lxvrc"])
    async def recruitcheck(self, ctx, member: discord.Member):
        """
        Check recruit status of member
        """
        role = discord.utils.get(member.roles, id=self.lxv_recruit_id)
        count = await self.LXV_COLLECTION.count_documents({"_id": "lxvrecruit"})
        old_data = await self.LXV_COLLECTION.find_one({"_id": "lxvrecruit"})
        data_id = f"user{member.id}"
        current_date = datetime.datetime.utcnow()
        if not count:
            await ctx.send("Empty database. Please initialize with s!forcerefresh")
        old_data = old_data["members"]

        if role is None and data_id not in old_data:
            return await ctx.send("User doesn't have role here neither in database")
        if role is not None and data_id not in old_data:
            return await ctx.send("User have the role but doesn't exist in database. "
                                  "For staff please do s!forcerefresh")
        if role is None and data_id in old_data:
            await ctx.send("User doesn't have role but exist in database. For staff consider doing s!forcerefresh")
        custom_embed = discord.Embed(title="Recruit info",
                                     description=f"Recruit since: {old_data[data_id]} "
                                                 f"({(current_date - old_data[data_id]).days} days)\n"
                                                 f"Other format:\n"
                                                 f"{discord.utils.format_dt(old_data[data_id], 'T')}\n"
                                                 f"{discord.utils.format_dt(old_data[data_id], 'd')}\n"
                                                 f"{discord.utils.format_dt(old_data[data_id], 'D')}\n"
                                                 f"{discord.utils.format_dt(old_data[data_id], 'f')}\n"
                                                 f"{discord.utils.format_dt(old_data[data_id], 'F')}\n"
                                                 f"{discord.utils.format_dt(old_data[data_id], 'R')}\n"
                                                 f"Nothing to show again? Just do s!whois",
                                     color=discord.Colour.random())
        await ctx.send(embed=custom_embed)

    @commands.command(hidden=True)
    async def setlxvrecruitid(self, ctx, role_id):
        if self.bot.owner != ctx.author:
            allowed = False
            for x in ctx.author.roles:
                if x.id in self.mod_ids:
                    allowed = True
                    break
            if not allowed:
                return await ctx.send("You are not allowed to use this command >:(")
        self.lxv_recruit_id = role_id
        return await ctx.send("Success")

    @commands.command(hidden=True)
    async def setlxvloggingid(self, ctx, channel_id):
        if self.bot.owner != ctx.author:
            allowed = False
            for x in ctx.author.roles:
                if x.id in self.mod_ids:
                    allowed = True
                    break
            if not allowed:
                return await ctx.send("You are not allowed to use this command >:(")
        self.logging_channel_id = channel_id
        return await ctx.send("Success")

    @commands.is_owner()
    @commands.command(hidden=True)
    async def lxveval(self, ctx, var):
        return await ctx.send(eval(var))


async def setup(bot: SewentyBot):
    await bot.add_cog(LoveSick(bot))
