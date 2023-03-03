from __future__ import annotations

from typing import TYPE_CHECKING, List

from copy import deepcopy
import datetime
import logging
import re

import discord
from discord.ext import commands, tasks

from utils import paginators
from utils.view_util import Dropdown, ConfirmEmbed, BaseView

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


# TODO: Move this to view_util, Fix inconsistent self var
class QueryDropdown(Dropdown):
    def __init__(self, text: str, select_list: List[discord.SelectOption]):
        super().__init__(text, select_list)
        self.selected = None
        self.ctx = None

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("You are not allowed to do this :c", ephemeral=True)
        self.selected = self.values[0]
        self.disabled = True
        self.view.stop()
        await interaction.response.edit_message(view=self.view)


class LoveSick(commands.Cog):
    GUILD_ID = 714152739252338749

    def __init__(self, bot: SewentyBot):
        self.bot: SewentyBot = bot
        self.LXV_COLLECTION = self.bot.DB["lovesick"]
        self.BLUEPRINT = {
            "added": [],
            "expired": [],
            "deleted": []
        }

        self.logging_channel_id = 0
        self.lxv_recruit_id = 0
        self.mod_ids = set()
        self.counter = -1
        self.last_checked = None
        self.recruit_log = deepcopy(self.BLUEPRINT)

    def cog_check(self, ctx) -> bool:
        return ctx.guild.id == self.GUILD_ID

    async def cog_load(self) -> None:
        setting = await self.LXV_COLLECTION.find_one({"_id": "setting"})
        if not setting:
            logger.error("No setting for lovesick found. Unloading cog...")
            await self.bot.remove_cog("extensions.lovesick")
        # Note that id always stored in str due to big number
        self.logging_channel_id = int(setting["logging_channel_id"])
        self.lxv_recruit_id = int(setting["lxv_recruit_id"])
        self.mod_ids = set(map(int, setting["mod_ids"]))
        self.refresh_lxv_recruit.start()

    async def cog_unload(self) -> None:
        self.refresh_lxv_recruit.cancel()

    @tasks.loop(hours=12)
    async def refresh_lxv_recruit(self):
        if self.bot.TEST_MODE:
            return
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

    def mod_only(self, ctx):
        allowed = False
        if self.bot.owner == ctx.author:
            allowed = True
        else:
            for x in ctx.author.roles:
                if x.id in self.mod_ids:
                    allowed = True
                    break
        return allowed

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
        if not self.mod_only(ctx):
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

    @commands.command(aliases=["lxvafr"])
    async def accuraterefresh(self, ctx, limit=100):
        """
        Accurete refresh for recruits date by checking audit log
        """
        if limit > 1000:
            return await ctx.send("Too big")
        if not self.mod_only(ctx):
            return await ctx.send("You are not allowed to use this command >:(")
        original = await ctx.send("Please wait <a:discordloading:792012369168957450>")
        count = await self.LXV_COLLECTION.count_documents({"_id": "lxvrecruit"})
        old_data = await self.LXV_COLLECTION.find_one({"_id": "lxvrecruit"})
        channel = ctx.guild.get_channel(self.logging_channel_id)

        if not count:
            old_data = dict()
        else:
            old_data = old_data["members"]
        new_data = dict()
        async for x in ctx.guild.audit_logs(limit=limit, action=discord.AuditLogAction.member_role_update):
            tmp_id = f"user{x.target.id}"
            if tmp_id in new_data:
                continue
            check_date = None
            for y in x.after.roles:
                if y.id == self.lxv_recruit_id:
                    check_date = x.created_at
            if check_date is None:
                continue
            new_data.update({tmp_id: check_date})
        merged_data = {**old_data, **new_data}
        if not count:
            await self.LXV_COLLECTION.insert_one({"_id": "lxvrecruit", "members": merged_data})
        else:
            await self.LXV_COLLECTION.update_one({"_id": "lxvrecruit"}, {"$set": {"members": merged_data}})
        self.counter += 1
        await original.edit(content="Done <:wurk:858721776770744320>")
        await channel.send(f"{ctx.author} used accurate refresh command with limit of last {limit} audit log")

    @commands.is_owner()
    @commands.command(hidden=True)
    async def lxveval(self, ctx, var):
        return await ctx.send(eval(var))

    @commands.group(invoke_without_command=True, aliases=["ev"])
    async def event(self, ctx):
        await ctx.send("This is event command. All pet event command will be grouped here (WIP)")

    @event.command(aliases=["f"])
    async def focus(self, ctx, *pet):
        if not self.mod_only(ctx):
            return await ctx.send("You are not allowed to use this command >:(")
        res = set()
        for p in pet:
            res.add(p.lower())
        custom_embed = discord.Embed(title="Focus index",
                                     description=f"Are you sure want to focus to index `{'`, `'.join(list(res))}`?",
                                     color=discord.Colour.green())
        confirm = ConfirmEmbed(ctx.author.id, custom_embed)
        await confirm.send(ctx)
        await confirm.wait()
        if not confirm.value:
            return
        await self.LXV_COLLECTION.update_one({"_id": "setting"}, {"$set": {"focus": list(res)}})
        await ctx.send("Updated focus")

    @event.command(aliases=["lb"])
    async def leaderboard(self, ctx, pet, length=5):
        if length < 1 or length > 10:
            return await ctx.send("Invalid number")
        pet = pet.lower()
        cursor = await self.LXV_COLLECTION.find_one({"_id": f"pet{pet}"})
        if not cursor:
            return await ctx.send("No leaderboard found")
        top = dict(sorted(cursor["participants"].items(), key=lambda x: x[1], reverse=True))
        custom_embed = discord.Embed(title=f"Leaderboard for pet {pet}", color=discord.Colour.random())
        for i, item in enumerate(top):
            custom_embed.add_field(name=f"#{i+1}: {ctx.guild.get_member(int(item))}",
                                   value=f"{top[item]} Hunts",
                                   inline=False)
            if i+1 >= length:
                break
        await ctx.send(embed=custom_embed)

    @event.command(aliases=["ac"])
    async def addcount(self, ctx: commands.Context, link):
        pattern = re.compile(
            r"https?://(?:(?:ptb|canary)\.)?discord(?:app)?\.com"
            r"/channels/(?P<guild_id>[0-9]{15,19})/(?P<channel_id>"
            r"[0-9]{15,19})/(?P<message_id>[0-9]{15,19})/?"
        )
        res = re.match(pattern, link)
        if res is None or not res.group(0):
            return await ctx.send("Invalid link")
        guild_id = int(res.group("guild_id"))
        channel_id = int(res.group("channel_id"))
        message_id = int(res.group("message_id"))
        if guild_id != self.GUILD_ID:
            return await ctx.send("Not from lxv guild")
        setting = await self.LXV_COLLECTION.find_one({"_id": "setting"})
        if "focus" not in setting or not setting["focus"]:
            return await ctx.send("No focus pet currently. Please add by s!focus")

        original = await ctx.send("Checking <a:discordloading:792012369168957450>")

        focus = setting["focus"]
        channel = ctx.guild.get_channel(channel_id)
        message: discord.Message = await channel.fetch_message(message_id)
        content = message.content.lower()
        if message.embeds:
            content = message.embeds[0].description.lower()
        content = content.split('|')
        username = content[1]
        check = 1
        if re.match(r".*\[[0-9]*/[0-9]*].*", content[check]):
            check += 1
        # Y u better not mess up with username
        found = username.rfind("**,") if check > 1 else username.find("** ")
        username = username[:found].strip()
        query = await ctx.guild.query_members(username)
        userid = str(query[0].id)
        if len(query) > 1:
            dropdown = QueryDropdown(text="Select username",
                                     select_list=[discord.SelectOption(label=str(member), value=str(member.id))
                                                  for member in query])
            view = BaseView()
            view.add_item(dropdown)
            check = await ctx.send(content="Multiple username found", view=view)
            dropdown.ctx = ctx
            await view.wait()
            userid = dropdown.selected
            await check.delete()
        skipped = []
        for pet in focus:
            res = content[check].count(pet)
            if res == 0:
                skipped.append(pet)
                continue
            participants = dict()
            form = {"_id": f"pet{pet}"}
            cursor = await self.LXV_COLLECTION.find_one(form)
            if cursor:
                participants = cursor["participants"]
            if userid in participants:
                res += participants[userid]
            participants.update({userid: res})
            if not cursor:
                await self.LXV_COLLECTION.insert_one({"_id": f"pet{pet}", "participants": participants})
            else:
                await self.LXV_COLLECTION.update_one(form, {"$set": {"participants": participants}})
        await original.edit(content=f"Done <:wurk:858721776770744320>\n"
                                    f"Skipped focus pet: `{'`, `'.join(skipped or ['None'])}`")

    @addcount.error
    async def addcount_on_error(self, ctx, error):
        custom_embed = discord.Embed(title="Failed to add count",
                                     description=error.original
                                     if isinstance(error, commands.CommandInvokeError)
                                     else error,
                                     color=discord.Colour.red())
        await ctx.send(embed=custom_embed)
        await self.bot.send_owner(f"Failed to addcount: {error.__traceback__}")


async def setup(bot: SewentyBot):
    await bot.add_cog(LoveSick(bot))
