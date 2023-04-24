from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

import asyncio
from copy import deepcopy
import datetime
from io import BytesIO
import logging
import re
from traceback import format_exception

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


class EditCount(BaseView):
    def __init__(self, parentcls: LoveSick, message: discord.Message, staff: discord.Member):
        super().__init__()
        self.parentcls = parentcls
        self.message = message
        self.lines = message.embeds[0].fields[0].value.split('\n')
        self.original = int(self.lines[0].split("**")[1])
        self.value = self.original
        self.userid = self.lines[1].split(':')[1].strip()
        self.staff = staff

    @discord.ui.button(emoji='🔼', style=discord.ButtonStyle.blurple)
    async def incre_number(self, interaction: discord.Interaction, _: discord.Button):
        self.value += 1
        await interaction.response.edit_message(content=f"Current value: **{self.value}**")

    @discord.ui.button(emoji='🔽', style=discord.ButtonStyle.blurple)
    async def decre_number(self, interaction: discord.Interaction, _: discord.Button):
        self.value -= 1
        self.value = max(0, self.value)
        await interaction.response.edit_message(content=f"Current value: **{self.value}**")

    @discord.ui.button(emoji='✅', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, _: discord.Button):
        difference = self.value - self.original
        cursor = await self.parentcls.LXV_COLLECTION.find_one(self.parentcls.pet_query)
        await interaction.response.defer()
        await interaction.delete_original_response()

        if cursor is None:
            return await interaction.followup.send("Index not found", ephemeral=True)
        participants = cursor["participants"]
        if self.userid not in participants:
            return await interaction.followup.send("User not found", ephemeral=True)

        participants.update({self.userid: participants[self.userid] + difference})
        await self.parentcls.LXV_COLLECTION.update_one(self.parentcls.pet_query,
                                                       {"$set": {"participants": participants}})
        custom_embed = self.message.embeds[0]
        self.lines[0] = f"Detected count: **{self.value}**"
        self.lines[1] = f"User id: {self.userid}"
        custom_embed.set_field_at(0, name="Detail", value='\n'.join(self.lines))
        await self.message.edit(content=f"Corrected by {self.staff}", embed=custom_embed)

    @discord.ui.button(label="Delete hunt", style=discord.ButtonStyle.red)
    async def delete_hunt(self, interaction: discord.Interaction, _: discord.Button):
        cursor = await self.parentcls.LXV_COLLECTION.find_one(self.parentcls.pet_query)
        await interaction.response.defer()
        await interaction.delete_original_response()

        if cursor is None:
            return await interaction.followup.send("Index not found", ephemeral=True)
        participants = cursor["participants"]
        if self.userid not in participants:
            return await interaction.followup.send("User not found", ephemeral=True)

        participants.update({self.userid: participants[self.userid]-self.original})
        await self.parentcls.LXV_COLLECTION.update_one(self.parentcls.pet_query,
                                                       {"$set": {"participants": participants}})

        await self.message.delete()


class ConfirmEdit(BaseView):
    def __init__(self, parentcls: LoveSick, message: discord.Message, staff: discord.Member):
        super().__init__()
        self.parentcls = parentcls
        self.message = message
        self.staff = staff
        self.view_msg = None

    @discord.ui.button(emoji='✅', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, _: discord.Button):
        if interaction.user.id != self.staff.id:
            return await interaction.response.send_message(content="You are not allowed to use this >:(",
                                                           ephemeral=True)
        await interaction.response.defer()
        view = EditCount(self.parentcls, self.message, self.staff)
        await interaction.delete_original_response()
        await interaction.followup.send(view=view, ephemeral=True)
        self.stop()

    @discord.ui.button(emoji='❎', style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, _: discord.Button):
        if interaction.user.id != self.staff.id:
            return await interaction.response.send_message(content="You are not allowed to use this >:(",
                                                           ephemeral=True)
        await interaction.response.defer()
        await interaction.delete_original_response()
        self.stop()

    async def send(self):
        self.view_msg = await self.message.reply(content="Confirm editing?", view=self)

    async def on_timeout(self) -> None:
        if self.view_msg is not None:
            await self.view_msg.delete()


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
        self.lxv_member_id = 0
        self.lxv_link_channel = 0
        self.event_link_channel = 0
        self.mod_ids = set()
        self.focus = []
        self.ignored = set()
        self.verified = set()
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
        self.lxv_member_id = int(setting["lxv_member_id"])
        self.lxv_link_channel = int(setting["lxv_link_channel"])
        self.event_link_channel = int(setting["event_link_channel"])
        self.mod_ids = set(map(int, setting["mod_ids"]))
        verified = await self.LXV_COLLECTION.find_one({"_id": "verified_msg"})
        if verified:
            self.verified = set(map(int, verified["msg_ids"]))
        self.focus = setting["focus"]
        self.focus.sort()
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
                return await self.bot.send_owner(f"Logging channel for lxv is missing. Old: {self.logging_channel_id}\n"
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
        if channel is None:
            return await self.bot.send_owner(f"Logging channel for lxv is missing. Old: {self.logging_channel_id}")
        ch = guild.get_channel(765818685922213948)
        await ch.send("Update data completed")

    @refresh_lxv_recruit.before_loop
    async def check_connected(self):
        logger.info("Waiting for bot...")
        await self.bot.wait_until_ready()

    @property
    def pet_query(self) -> dict:
        return {"_id": f"pet|{'|'.join(self.focus)}"}

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

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if (
                payload.guild_id == self.GUILD_ID and payload.emoji.name == '📝' and
                payload.channel_id in {self.lxv_link_channel, self.event_link_channel}
                and payload.message_id not in self.ignored
                and payload.user_id not in self.ignored
        ):
            guild = self.bot.get_guild(self.GUILD_ID)
            channel = guild.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)

            if message.author.id != self.bot.user.id:
                self.ignored.add(payload.message_id)
                return

            member = guild.get_member(payload.user_id)
            if member is None:  # Fallback
                member = guild.fetch_member(payload.user_id)

            allowed = False
            if self.bot.owner == member:
                allowed = True
            else:
                for x in member.roles:
                    if x.id in self.mod_ids:
                        allowed = True
                        break

            if not allowed:
                self.ignored.add(payload.user_id)
                return

            view = ConfirmEdit(self, message, member)
            await view.send()

        if (
                payload.guild_id == self.GUILD_ID
                and payload.emoji.id == 1046848826050359368
                and payload.message_id not in self.ignored
                and payload.message_id not in self.verified
                and (payload.user_id, payload.message_id) not in self.ignored
        ):
            guild = self.bot.get_guild(self.GUILD_ID)
            channel = guild.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)

            # Check if its from owo
            if message.author.id != 408785106942164992:
                self.ignored.add(payload.message_id)
                return

            userid = str(payload.user_id)
            member = guild.get_member(payload.user_id)
            if member is None:  # Fallback
                member = guild.fetch_member(payload.user_id)

            link_channel = guild.get_channel(self.lxv_link_channel
                                             if member.get_role(self.lxv_member_id) else self.event_link_channel)

            content = message.content.lower() if not message.embeds else message.embeds[0].description.lower()

            if member.name not in content:
                await message.reply("Username doesn't match/found in hunting message. "
                                    "If you believe this is yours, contact staff")
                self.ignored.add((payload.user_id, payload.message_id))
                return

            default = 1
            counts = 0
            """
                Normal content would be
                x | name hunt   [0]
                y | caught pets [1]
                z | team xp     [2]
                """
            check = content.split('\n')
            for i, line in enumerate(check):
                for pet in self.focus:
                    if pet in line:
                        if i == default:
                            counts += line.count(pet)

                        if i != default and not line.endswith("**!"):  # default message for xp team
                            default = i
                            counts = line.count(pet)

            participants = {}
            if counts == 0:
                return await message.reply("No event pet found")
            detected = counts
            cursor = await self.LXV_COLLECTION.find_one(self.pet_query)
            if cursor:
                participants = cursor["participants"]
            if userid in participants:
                counts += participants[userid]
            participants.update({userid: counts})

            link_embed = discord.Embed(title=f"Hunt from {member}", description=content,
                                       color=discord.Colour.green())
            link_embed.add_field(name="Detail",
                                 value=f"Detected count: **{detected}**\n"
                                       f"User id: {userid}\n"
                                       f"Jump url: [Link]({message.jump_url})\n"
                                       f"If anything wrong, react the emoji below")
            msg = await link_channel.send(embed=link_embed)
            await msg.add_reaction('📝')

            if not cursor:
                await self.LXV_COLLECTION.insert_one(
                    {"_id": f"pet|{'|'.join(self.focus)}", "participants": participants})
            else:
                await self.LXV_COLLECTION.update_one(self.pet_query, {"$set": {"participants": participants}})

            self.verified.add(payload.message_id)
            verified = await self.LXV_COLLECTION.find_one({"_id": "verified_msg"})
            if not verified:
                await self.LXV_COLLECTION.insert_one({"_id": "verified_msg", "msg_ids": list(self.verified)})
            else:
                await self.LXV_COLLECTION.update_one({"_id": "verified_msg"},
                                                     {"$set": {"msg_ids": list(self.verified)}})
            await message.reply(f"Sent to {link_channel.mention}")

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

        await ctx.send("Successfully force refreshed")

    @commands.command()
    async def lxv(self, ctx):
        custom_embed = discord.Embed(title="This looks cool",
                                     description=f"Last updated: {self.last_checked}",
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
        await original.edit(content="Done <:wurk:858721776770744320>")
        await channel.send(f"{ctx.author} used accurate refresh command with limit of last {limit} audit log")

    @commands.command()
    async def lxvrefresh(self, ctx):
        if not self.mod_only(ctx):
            return await ctx.send("Huh")
        original = await ctx.send("Refreshing <a:discordloading:792012369168957450>")
        setting = await self.LXV_COLLECTION.find_one({"_id": "setting"})
        if not setting:
            return await ctx.send("ERROR: Setting doen't exist at database")
        self.logging_channel_id = int(setting["logging_channel_id"])
        self.lxv_recruit_id = int(setting["lxv_recruit_id"])
        self.lxv_member_id = int(setting["lxv_member_id"])
        self.lxv_link_channel = int(setting["lxv_link_channel"])
        self.event_link_channel = int(setting["event_link_channel"])
        self.mod_ids = set(map(int, setting["mod_ids"]))
        verified = await self.LXV_COLLECTION.find_one({"_id": "verified_msg"})
        if verified:
            self.verified = set(map(int, verified["msg_ids"]))
        self.focus = setting["focus"]
        self.focus.sort()
        await original.edit(content="Done <:wurk:858721776770744320>")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def lxvlog(self, ctx, *, message):
        guild = self.bot.get_guild(self.GUILD_ID)
        channel = guild.get_channel(self.logging_channel_id)
        await channel.send(f"LOGGING from {ctx.author}: {message}")
        await ctx.message.add_reaction('👍')

    @commands.command(hidden=True)
    @commands.is_owner()
    async def lxveval(self, ctx, var):
        return await ctx.send(eval(var))

    @commands.group(invoke_without_command=True, aliases=["ev"])
    async def event(self, ctx):
        await ctx.send(f"Hi event\n"
                       f"For detail command, check from `s!help event` and `s!help event [command]` for detail\n"
                       f"||Read the command detail before use 👀||\n"
                       f"Focused pet: `{'` `'.join(self.focus or ['None'])}`")

    @event.command(aliases=["f"])
    async def focus(self, ctx, *pet):
        """
        Set focus pet. For multiple pet just separate by space
        Warning: if you use addcountuser without pet specified, all the count will deleted
        """
        if not self.mod_only(ctx):
            return await ctx.send("You are not allowed to use this command >:(")
        res = set()
        for p in pet:
            res.add(p.lower())
        if not pet:
            res = ["None"]
        res = list(res)
        res.sort()
        custom_embed = discord.Embed(title="Focus index",
                                     description=f"Are you sure want to focus to index `{'`, `'.join(res)}`?\n"
                                                 f"**All verified message id posted at link will be deleted**",
                                     color=discord.Colour.green())
        confirm = ConfirmEmbed(ctx.author.id, custom_embed)
        await confirm.send(ctx)
        await confirm.wait()
        if not confirm.value:
            return
        self.focus = res
        self.verified = set()
        await self.LXV_COLLECTION.update_one({"_id": "verified_msg"}, {"$set": {"msg_ids": []}})
        await self.LXV_COLLECTION.update_one({"_id": "setting"}, {"$set": {"focus": list(res)}})

    @event.command(aliases=["s"])
    async def stat(self, ctx, user: Optional[discord.User] = None):
        """
        Show pet count
        """
        if user is None:
            user = ctx.author
        userid = str(user.id)
        cursor = await self.LXV_COLLECTION.find_one(self.pet_query)
        if not self.focus:
            return await ctx.send("No focus pet currently")
        if not cursor:
            return await ctx.send("No pet index found")
        counts = cursor["participants"].get(userid, 0)
        await ctx.send(f"Total hunt: **{counts}**")

    @event.command(aliases=["lb"])
    async def leaderboard(self, ctx, length=5):
        """
        Show pet leaderboard. Will sum all focus pet hunt if not specified
        """
        if not self.mod_only(ctx):
            return await ctx.send("You are not allowed to use this command >:(")
        if length < 1 or length > 10:
            return await ctx.send("Invalid number")
        if not self.focus:
            return await ctx.send("No focus pet currently. Please add by s!focus")
        cursor = await self.LXV_COLLECTION.find_one(self.pet_query)
        if not cursor:
            return await ctx.send("No leaderboard found")
        top = cursor["participants"]
        top = dict(sorted(top.items(), key=lambda it: it[1]))
        custom_embed = discord.Embed(title=f"Leaderboard", color=discord.Colour.random())
        i = 1
        for userid, item in top.items():
            custom_embed.add_field(name=f"#{i}: {ctx.guild.get_member(int(userid))}",
                                   value=f"{item} Hunts",
                                   inline=False)
            i += 1
            if i > length:
                break
        await ctx.send(embed=custom_embed)

    # @event.command(aliases=["ac"])
    # async def addcount(self, ctx: commands.Context, link):
    #     pattern = re.compile(
    #         r"https?://(?:(?:ptb|canary)\.)?discord(?:app)?\.com"
    #         r"/channels/(?P<guild_id>[0-9]+)/(?P<channel_id>"
    #         r"[0-9]+)/(?P<message_id>[0-9]+)"
    #     )
    #     res = re.match(pattern, link)
    #     if res is None or not res.group(0):
    #         return await ctx.send("Invalid link")
    #     guild_id = int(res.group("guild_id"))
    #     channel_id = int(res.group("channel_id"))
    #     message_id = int(res.group("message_id"))
    #     if guild_id != self.GUILD_ID:
    #         return await ctx.send("Not from lxv guild")
    #     if not self.focus:
    #         return await ctx.send("No focus pet currently. Please add by s!focus")
    #
    #     original = await ctx.send("Checking <a:discordloading:792012369168957450>")
    #
    #     channel = ctx.guild.get_channel(channel_id)
    #     message: discord.Message = await channel.fetch_message(message_id)
    #     if message.embeds and message.embeds[0].description is None:
    #         return await ctx.send("Unable to check the first embed description. Is that right embed?")
    #     content = message.content.lower() if not message.embeds else message.embeds[0].description.lower()
    #     userid = None
    #     if message.embeds and message.embeds[0].author.icon_url:
    #         cdnpattern = re.compile(
    #             r"https?://(media|cdn)\.discord(?:app)?\.com"
    #             r"/avatars/(?P<userid>[0-9]+)"
    #             r"/(?P<hash>([0-9]+)[\S]+)\?(?P<parameter>.+)"
    #         )
    #         cdnres = re.match(cdnpattern, message.embeds[0].author.icon_url)
    #         if cdnres is None or not cdnres.group(0):
    #             return await ctx.send("User profile not found in custom hunt. Wrong link?")
    #         userid = cdnres.group("userid")
    #     elif not message.embeds:
    #         # Assuming non-custom hunt
    #         section = content.split('|')
    #         new_line = True if re.match(r".*\[[0-9]*/[0-9]*].*", section[1]) else False
    #         username = section[1]
    #         # Y u better not mess up with username
    #         found = username.rfind("**,") if new_line else username.find("** ")
    #         username = username[:found].strip()
    #         query = await ctx.guild.query_members(username)
    #         if query:
    #             userid = str(query[0].id)
    #             if len(query) > 1:
    #                 dropdown = QueryDropdown(text="Select username",
    #                                          select_list=[discord.SelectOption(label=str(member), value=str(member.id))
    #                                                       for member in query])
    #                 view = BaseView()
    #                 view.add_item(dropdown)
    #                 check = await ctx.send(content="Multiple username found", view=view)
    #                 dropdown.ctx = ctx
    #                 await view.wait()
    #                 userid = dropdown.selected
    #                 await check.delete()
    #     else:
    #         await ctx.send("Kindly enable the profile icon for custom hunt :)))")
    #     if userid is None:
    #         await original.edit(content="No userid found. Please input the userid (input 0 to abort)")
    #         userid = await self.bot.wait_for("message",
    #                                          check=lambda x: x.author == ctx.author and x.content.isdecimal())
    #         userid = userid.content
    #         if userid == '0':
    #             return await original.edit(content="Aborted")
    #     skipped = []
    #     should_be = 1
    #     check = content.split('\n')
    #     if message.embeds:
    #         for i, line in enumerate(check):
    #             for pet in self.focus:
    #                 if pet in line:
    #                     if should_be is not None and i != should_be:
    #                         await original.edit(content=f"Detect pet confusion. "
    #                                                     f"Please input correct line **{should_be+1}** or **{i+1}**")
    #                         should_be = await self.bot.wait_for("message",
    #                                                             check=lambda x:
    #                                                             x.author == ctx.author and x.content.isdecimal()
    #                                                             and int(x.content) in {should_be, line})
    #                         should_be = int(should_be.content)-1
    #                         break
    #                     should_be = i
    #     for pet in self.focus:
    #         res = check[should_be].count(f"{pet}")
    #         if res == 0:
    #             skipped.append(pet)
    #             continue
    #         participants = dict()
    #         form = {"_id": f"pet{pet}"}
    #         cursor = await self.LXV_COLLECTION.find_one(form)
    #         if cursor:
    #             participants = cursor["participants"]
    #         if userid in participants:
    #             res += participants[userid]
    #         participants.update({userid: res})
    #         if not cursor:
    #             await self.LXV_COLLECTION.insert_one({"_id": f"pet{pet}", "participants": participants})
    #         else:
    #             await self.LXV_COLLECTION.update_one(form, {"$set": {"participants": participants}})
    #     await original.edit(content=f"Done <:wurk:858721776770744320>\n"
    #                                 f"Skipped focus pet: `{'`, `'.join(skipped or ['None'])}`")
    #
    # @addcount.error
    # async def addcount_on_error(self, ctx, error):
    #     custom_embed = discord.Embed(title="Failed to add count",
    #                                  description=error.original
    #                                  if isinstance(error, commands.CommandInvokeError)
    #                                  else error,
    #                                  color=discord.Colour.red())
    #     await ctx.send(embed=custom_embed)
    #     output = ''.join(format_exception(type(error), error, error.__traceback__))
    #     if len(output) > 1500:
    #         buffer = BytesIO(output.encode("utf-8"))
    #         file = discord.File(buffer, filename="log.txt")
    #         await self.bot.send_owner(file=file)
    #     else:
    #         custom_embed = discord.Embed(title="Addcount fail", description=f"```py\n{output}```",
    #                                      color=discord.Colour.red())
    #         await self.bot.send_owner(embed=custom_embed)
    #
    # @event.command(aliases=["acf"])
    # async def addcountfrom(self, ctx, link):
    #     """
    #     Start counting link that posted after specified link message **(not the link itself)**
    #     Mean if you want to start at message X, then you need to get message link **before** that message X
    #     """
    #     if not self.mod_only(ctx):
    #         return await ctx.send("You are not allowed to use this command >:(")
    #
    #     pattern = re.compile(
    #         r"https?://(?:(?:ptb|canary)\.)?discord(?:app)?\.com"
    #         r"/channels/(?P<guild_id>[0-9]+)/(?P<channel_id>"
    #         r"[0-9]+)/(?P<message_id>[0-9]+)"
    #     )
    #     res = re.match(pattern, link)
    #     if res is None or not res.group(0):
    #         return await ctx.send("Invalid link")
    #     guild_id = int(res.group("guild_id"))
    #     channel_id = int(res.group("channel_id"))
    #     message_id = int(res.group("message_id"))
    #     if guild_id != self.GUILD_ID:
    #         return await ctx.send("Not from lxv guild")
    #     if not self.focus:
    #         return await ctx.send("No focus pet currently. Please add by s!focus")
    #
    #     original = await ctx.send("Checking <a:discordloading:792012369168957450>")
    #
    #     channel: discord.TextChannel = ctx.guild.get_channel(channel_id)
    #     snowflake = discord.utils.snowflake_time(message_id)
    #     async for message in channel.history(after=snowflake, oldest_first=True):
    #         msglink = message.content
    #         if message.embeds:
    #             if not message.embeds[0].fields:
    #                 await message.add_reaction("<:Kannaconfused:799040710770032670>")
    #                 await asyncio.sleep(3)
    #                 continue
    #             msglink = message.embeds[0].fields[-1].value
    #         if not msglink:
    #             await message.add_reaction("<:Kannaconfused:799040710770032670>")
    #             await asyncio.sleep(3)
    #             continue
    #         msgres = re.search(pattern, msglink)
    #         if msgres is None:
    #             await message.add_reaction("<:Kannaconfused:799040710770032670>")
    #             await asyncio.sleep(3)
    #             continue
    #
    #         msg_guild_id = int(msgres.group("guild_id"))
    #         msg_channel_id = int(msgres.group("channel_id"))
    #         msg_message_id = int(msgres.group("message_id"))
    #
    #         if msg_guild_id != self.GUILD_ID:
    #             await message.add_reaction("<:Kannaconfused:799040710770032670>")
    #             await asyncio.sleep(3)
    #             continue
    #
    #         msg_channel = ctx.guild.get_channel(msg_channel_id)
    #         msg_message: discord.Message = await msg_channel.fetch_message(msg_message_id)
    #         if msg_message.embeds and msg_message.embeds[0].description is None:
    #             await message.add_reaction("<:Kannaconfused:799040710770032670>")
    #             await asyncio.sleep(3)
    #             continue
    #
    #         content = (msg_message.content.lower() if not msg_message.embeds
    #                    else msg_message.embeds[0].description.lower())
    #         userid = None
    #
    #         if msg_message.embeds and msg_message.embeds[0].author.icon_url:
    #             cdnpattern = re.compile(
    #                 r"https?://(media|cdn)\.discord(?:app)?\.com"
    #                 r"/avatars/(?P<userid>[0-9]+)"
    #                 r"/(?P<hash>([0-9]+)[\S]+)\?(?P<parameter>.+)"
    #             )
    #             cdnres = re.match(cdnpattern, msg_message.embeds[0].author.icon_url)
    #             if cdnres is None or not cdnres.group(0):
    #                 await message.add_reaction("<:Kannaconfused:799040710770032670>")
    #                 await asyncio.sleep(3)
    #                 continue
    #             userid = cdnres.group("userid")
    #         elif not msg_message.embeds:
    #             # Assuming non-custom hunt
    #             section = content.split('|')
    #             new_line = True if re.match(r".*\[[0-9]*/[0-9]*].*", section[1]) else False
    #             username = section[1]
    #             # Y u better not mess up with username
    #             found = username.rfind("**,") if new_line else username.find("** ")
    #             username = username[:found].strip()
    #             query = await ctx.guild.query_members(username)
    #             if query:
    #                 userid = str(query[0].id)
    #                 if len(query) > 1:
    #                     await message.add_reaction("<:Kannaconfused:799040710770032670>")
    #                     await asyncio.sleep(3)
    #                     continue
    #         else:
    #             await message.add_reaction("<:Kannaconfused:799040710770032670>")
    #             await asyncio.sleep(3)
    #             continue
    #
    #         if userid is None:
    #             await message.add_reaction("<:Kannaconfused:799040710770032670>")
    #             await asyncio.sleep(3)
    #             continue
    #
    #         skipped = []
    #         should_be = 1
    #         check = content.split('\n')
    #         kindly_exit = False
    #         if message.embeds:
    #             for i, line in enumerate(check):
    #                 for pet in self.focus:
    #                     if pet in line:
    #                         if should_be is not None and i != should_be:
    #                             kindly_exit = True
    #                             break
    #                         should_be = i
    #                 if kindly_exit:
    #                     break
    #             if kindly_exit:
    #                 await message.add_reaction("<:Kannaconfused:799040710770032670>")
    #                 await asyncio.sleep(3)
    #                 continue
    #
    #         for pet in self.focus:
    #             res = check[should_be].count(f":{pet}:")
    #             if res == 0:
    #                 skipped.append(pet)
    #                 continue
    #             participants = dict()
    #             form = {"_id": f"pet{pet}"}
    #             cursor = await self.LXV_COLLECTION.find_one(form)
    #             if cursor:
    #                 participants = cursor["participants"]
    #             if userid in participants:
    #                 res += participants[userid]
    #             participants.update({userid: res})
    #             if not cursor:
    #                 await self.LXV_COLLECTION.insert_one({"_id": f"pet{pet}", "participants": participants})
    #             else:
    #                 await self.LXV_COLLECTION.update_one(form, {"$set": {"participants": participants}})
    #         await message.add_reaction("<:wurk:858721776770744320>")
    #         await asyncio.sleep(3)
    #     await original.edit(content="Done <:wurk:858721776770744320>")
    #
    # @addcountfrom.error
    # async def addcountfrom_on_error(self, ctx, error):
    #     custom_embed = discord.Embed(title="Failed to mass add count",
    #                                  description=error.original
    #                                  if isinstance(error, commands.CommandInvokeError)
    #                                  else error,
    #                                  color=discord.Colour.red())
    #     await ctx.send(embed=custom_embed)
    #     output = ''.join(format_exception(type(error), error, error.__traceback__))
    #     if len(output) > 1500:
    #         buffer = BytesIO(output.encode("utf-8"))
    #         file = discord.File(buffer, filename="log.txt")
    #         await self.bot.send_owner(file=file)
    #     else:
    #         custom_embed = discord.Embed(title="Addcountfrom fail", description=f"```py\n{output}```",
    #                                      color=discord.Colour.red())
    #         await self.bot.send_owner(embed=custom_embed)

    @event.command(aliases=["acu"])
    async def addcountuser(self, ctx, user: discord.User, amount: Optional[int] = 1):
        """
        Manual add count for user
        """
        if not self.mod_only(ctx):
            return await ctx.send("You are not allowed to use this command >:(")
        if amount < 0 or amount > 2147483647:
            return await ctx.send("Invalid number")
        cursor = await self.LXV_COLLECTION.find_one(self.pet_query)
        if not cursor:
            custom_embed = discord.Embed(title="Add count",
                                         description=f"Pet doesn't exist in database. "
                                                     f"Do you want to add index of focus pet?",
                                         color=discord.Colour.green())
            confirm = ConfirmEmbed(ctx.author.id, custom_embed)
            await confirm.send(ctx)
            await confirm.wait()
            if not confirm.value:
                return
        participants = cursor["participants"] if cursor else {}
        res = amount
        userid = str(user.id)
        if userid in participants:
            res += participants[userid]
        participants.update({userid: res})
        if not cursor:
            await self.LXV_COLLECTION.insert_one({"_id": f"pet|{'|'.join(self.focus)}", "participants": participants})
        else:
            await self.LXV_COLLECTION.update_one(self.pet_query, {"$set": {"participants": participants}})
        await ctx.send(f"Succesfully add count pet of user {user} by {amount}")

    @event.command(aliases=["sc"])
    async def setcount(self, ctx, user: discord.User, amount: Optional[int] = 0):
        """
        Set pet count of user. Amount 0 to delete the entry
        """
        if not self.mod_only(ctx):
            return await ctx.send("You are not allowed to use this command >:(")
        if amount < 0 or amount > 2147483647:
            return await ctx.send("Invalid number")
        userid = str(user.id)
        cursor = await self.LXV_COLLECTION.find_one(self.pet_query)
        if not cursor:
            return await ctx.send("Pet not found")
        participants: dict = cursor["participants"]
        if userid not in participants:
            return await ctx.send("User not found")
        custom_embed = discord.Embed(title="Set count",
                                     description=f"You are changing pet count of user {user} "
                                                 f"(Previous **{participants[userid]}**)\n"
                                                 f"Proceed to continue?",
                                     color=discord.Colour.green())
        confirm = ConfirmEmbed(ctx.author.id, custom_embed)
        await confirm.send(ctx)
        await confirm.wait()
        if not confirm.value:
            return
        if amount == 0:
            participants.pop(userid)
        else:
            participants.update({userid: amount})
        await self.LXV_COLLECTION.update_one(self.pet_query, {"$set": {"participants": participants}})


async def setup(bot: SewentyBot):
    await bot.add_cog(LoveSick(bot))
