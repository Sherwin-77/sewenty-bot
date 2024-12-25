from __future__ import annotations

import asyncio
import datetime
import random
from typing import TYPE_CHECKING, List, Optional, Union

import logging

import discord
from discord.ext import commands, tasks
import pytz

import utils.date
from utils.cache import MessageCache
from utils.paginators import DataEmbedSource, SimplePages
from utils.view_util import Dropdown, ConfirmEmbed, BaseView

if TYPE_CHECKING:
    from main import SewentyBot

logger = logging.getLogger(__name__)


# TODO: Move this to view_util, Fix inconsistent self var
class QueryDropdown(Dropdown):
    ctx: commands.Context

    def __init__(self, text: str, select_list: List[discord.SelectOption]):
        super().__init__(text, select_list)
        self.selected = None

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
        self.lines = message.embeds[0].fields[0].value.split('\n')  # type: ignore
        self.original = int(self.lines[0].split("**")[1])
        self.value = self.original
        self.userid = self.lines[1].split(':')[1].strip()
        self.staff = staff

    async def _delete_hunt(self, interaction: discord.Interaction):
        cursor = await self.parentcls.LXV_COLLECTION.find_one(self.parentcls.pet_query)
        if cursor is None:
            return await interaction.response.send_message("Index not found", ephemeral=True)
        participants = cursor["participants"]
        if self.userid not in participants:
            return await interaction.response.send_message("User not found", ephemeral=True)
        res = participants[self.userid] - self.original
        if res <= 0:
            participants.pop(self.userid)
        else:
            participants.update({self.userid: res})
        await self.parentcls.LXV_COLLECTION.update_one(self.parentcls.pet_query, {"$set": {"participants": participants}})

    @discord.ui.button(emoji='🔼', style=discord.ButtonStyle.blurple)  # type: ignore
    async def incre_number(self, interaction: discord.Interaction, _: discord.Button):
        self.value += 1
        await interaction.response.edit_message(content=f"Current value: **{self.value}**")

    @discord.ui.button(emoji='🔽', style=discord.ButtonStyle.blurple)  # type: ignore
    async def decre_number(self, interaction: discord.Interaction, _: discord.Button):
        self.value -= 1
        self.value = max(0, self.value)
        await interaction.response.edit_message(content=f"Current value: **{self.value}**")

    @discord.ui.button(emoji='✅', style=discord.ButtonStyle.green)  # type: ignore
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
        await self.parentcls.LXV_COLLECTION.update_one(self.parentcls.pet_query, {"$set": {"participants": participants}})
        custom_embed = self.message.embeds[0]
        self.lines[0] = f"Detected count: **{self.value}**"
        self.lines[1] = f"User id: {self.userid}"
        custom_embed.set_field_at(0, name="Detail", value='\n'.join(self.lines))
        await self.message.edit(content=f"Corrected by {self.staff}", embed=custom_embed)

    @discord.ui.button(label="Delete Hunt", style=discord.ButtonStyle.red)  # type: ignore
    async def delete_hunt(self, interaction: discord.Interaction, _: discord.Button):
        await interaction.response.defer()
        await interaction.delete_original_response()

        await self._delete_hunt(interaction)

        await self.message.delete()


class ConfirmEdit(BaseView):
    def __init__(self, parentcls: LoveSick, message: discord.Message, staff: discord.Member):
        super().__init__()
        self.parentcls = parentcls
        self.message = message
        self.staff = staff
        self.view_msg = None

    @discord.ui.button(emoji='✅', style=discord.ButtonStyle.green)  # type: ignore
    async def confirm(self, interaction: discord.Interaction, _: discord.Button):
        if interaction.user.id != self.staff.id:
            return await interaction.response.send_message(content="You are not allowed to use this >:(", ephemeral=True)
        await interaction.response.defer()
        view = EditCount(self.parentcls, self.message, self.staff)
        await interaction.delete_original_response()
        await interaction.followup.send(view=view, ephemeral=True)
        self.stop()

    @discord.ui.button(emoji='❌', style=discord.ButtonStyle.red)  # type: ignore
    async def cancel(self, interaction: discord.Interaction, _: discord.Button):
        if interaction.user.id != self.staff.id:
            return await interaction.response.send_message(content="You are not allowed to use this >:(", ephemeral=True)
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
        self.LXV_STAT_COLLECTION = self.bot.LXV_DB["owo-stats"]

        self.lxv_member_id = 0
        self.lxv_link_channel = 0
        self.event_link_channel = 0
        self.event_disabled = False
        self.lxv_only_event = False
        self.required_role_ids: List[Union[str, List[str]]] = []
        self.mod_ids = set()
        self.focus = []
        self.ignored = set()
        self.verified = set()
        self.owo_drop_event_settings = {}
        self._inactives_member_data = []
        self._last_inactive_check: Optional[datetime.datetime] = None
        self._next_inactive_check: Optional[datetime.datetime] = None
        self._inactive_interval_months = 0;
        self._drop_cd = set()
        self.item_render = {
            "Grinch gift": "<a:gift1:1186669830074531840>",
            "Wreath gift": "<a:gift2:1186669847095029781>",
            "Angel gift": "<a:gift3:1184120760374149201>",
            "Rudolph gift": "<a:gift4:1186669868947349515>",
            "Santa gift": "<a:gift5:1186669895665066064>",
        }
        self.gift_names = ["Grinch gift", "Wreath gift", "Angel gift", "Rudolph gift", "Santa gift"]
        self.randgen = random.SystemRandom()

    async def get_setting(self, unload_on_error=True):
        setting = await self.LXV_COLLECTION.find_one({"_id": "setting"})
        if not setting:
            if unload_on_error:
                logger.error("No setting for lovesick found. Unloading cog...")
                await self.bot.remove_cog("extensions.lovesick")
            else:
                logger.warning("No setting for lovesick found. Skipping setting check")
            return -1

        self.message_cache = MessageCache(50)
        self.mod_cache = set()

        # Note that id always stored in str due to big number
        self.lxv_member_id = int(setting["lxv_member_id"])
        self.lxv_link_channel = int(setting["lxv_link_channel"])
        self.event_link_channel = int(setting["event_link_channel"])
        self.lxv_only_event = setting["lxv_only_event"]
        self.mod_ids = set(map(int, setting["mod_ids"]))
        self.required_role_ids = setting["required_role_ids"]
        verified = await self.LXV_COLLECTION.find_one({"_id": "verified_msg"})
        if verified:
            self.verified = set(map(int, verified["msg_ids"]))
        self.event_disabled = setting["event_disabled"]
        self.focus = setting["focus"]
        self.focus.sort()
        return 0

    def cog_check(self, ctx) -> bool:
        return ctx.guild is not None and ctx.guild.id == self.GUILD_ID

    async def cog_load(self) -> None:
        await self.get_setting()
        self.auto_remove_member.start()
        self.ping_lxv_db.start()
        doc = await self.LXV_COLLECTION.find_one({"_id": "OwODropEvent"})
        self.owo_drop_event_settings = doc

    async def cog_unload(self) -> None:
        self.ping_lxv_db.cancel()
        self.auto_remove_member.cancel()

    @tasks.loop()
    async def auto_remove_member(self):
        auto_member_settings = await self.LXV_COLLECTION.find_one({"_id": "autoMember"})
        previous_check = await self.LXV_COLLECTION.find_one({"_id": "autoMemberCheck"})
        if previous_check is not None:
            self._last_inactive_check = previous_check["lastCheck"]
            self._inactives_member_data = previous_check["data"]
            logger.info("Found previous check, setting last check time to %s", self._last_inactive_check)

        guild = self.bot.get_guild(self.GUILD_ID)
        ch = guild.get_channel(789154199186702408)  # type: ignore
        if not auto_member_settings or "nextTime" not in auto_member_settings or "repeatEvery" not in auto_member_settings or "disabled" not in auto_member_settings:
            logger.warning("No schedule or invalid setting found. Stopping task")
            return self.auto_remove_member.stop()
        if auto_member_settings["disabled"]:
            logger.info("Disabled schedule")
            return self.auto_remove_member.stop()

        tz = pytz.timezone("US/Pacific")
        next_date = utils.date.reset_tz(auto_member_settings["nextTime"], tz)
        interval_months = auto_member_settings["repeatEvery"]
        self._next_inactive_check = next_date
        self._inactive_interval_months = interval_months

        # TODO: Maybe reminder for every member 3 days before check

        # Set reminder 1 day before execute
        await discord.utils.sleep_until(next_date - datetime.timedelta(days=1))
        await ch.send("**Auto Remove Member**: 1 day left before check!")  # type: ignore
        # Continue sleep
        await discord.utils.sleep_until(next_date)

        # Execute here
        msg = await ch.send("Loading <a:discordloading:792012369168957450>")  # type: ignore
        lxv_role = guild.get_role(self.lxv_member_id)  # type: ignore
        if lxv_role is None:
            await self.bot.send_owner(f"LXV Member id not found. Previously {self.lxv_member_id}")
            logger.warning("No member role found. Stopping task")
            return self.auto_remove_member.stop()
        # Get all ids of lxv member
        lxv_members_id = [x.id for x in lxv_role.members]

        # Get current running date id to substract later
        # NOTE: all owos only collected up until X day where X is interval of this schedule
        base_date = datetime.datetime(2000, 1, 1).replace(
            hour=0, minute=0, second=0, microsecond=0, tzinfo=tz
        )
        date_before = utils.date.reset_tz(utils.date.add_months(next_date, -interval_months, 1), tz)

        date_now_id = utils.date.absolute_day_diff(next_date, base_date)
        date_before_id = utils.date.absolute_day_diff(date_before, base_date)

        # Query to match all the id user that in lxv member id, then collect until x day before, then sum all of them
        query = {"$match": {"$and": [{"_id.user": {"$in": lxv_members_id}}, {"_id.dayId": {"$gte": date_before_id, "$lte": date_now_id}}]}}
        grouping = {"$group": {"_id": "$_id.user", "counts": {"$sum": "$owoCount"}}}

        # NOTE: Notice hardcode requirement owo
        raw = {x: 0 for x in lxv_members_id}
        async for row in self.LXV_STAT_COLLECTION.aggregate([query, grouping]):
            if row["counts"] >= 1000:
                raw.pop(row["_id"])
            else:
                raw[row["_id"]] = row["counts"]
        results = [{"id": mem.id, "name": mem.name, "count": raw[mem.id]} for mem in lxv_role.members if mem.id in raw]
        self._inactives_member_data = results
        self._last_inactive_check = discord.utils.snowflake_time(msg.id)
        await msg.edit(
            content="Checking member done. Please check list by using `s!lxv automember memberinfo`. If you are sure to remove their roles, execute by using `s!lxv automember execute`"
        )
        
        if previous_check is not None:
            await self.LXV_COLLECTION.update_one({"_id": "autoMemberCheck"}, {"$set": {"data": self._inactives_member_data, "lastCheck": self._last_inactive_check}})
        else:
            await self.LXV_COLLECTION.insert_one({"_id": "autoMemberCheck", "data": self._inactives_member_data, "lastCheck": self._last_inactive_check})

        # Update next time
        next_time = utils.date.reset_tz(utils.date.add_months(discord.utils.snowflake_time(msg.id), interval_months, 1), tz)
        await self.LXV_COLLECTION.update_one({"_id": "autoMember"}, {"$set": {"nextTime": next_time}})

    @auto_remove_member.before_loop
    async def member_check_connected(self):
        logger.info("Auto Member: Waiting for bot...")
        await self.bot.wait_until_ready()

    @tasks.loop(hours=12)
    async def ping_lxv_db(self):
        self.mod_cache.clear()
        stats = self.LXV_COLLECTION.aggregate([{"$collStats": {"latencyStats": {"histograms": False}}}])
        read_latency = []
        total_read = 0
        write_latency = []
        total_write = 0
        command_latency = []
        total_command = 0
        transaction_latency = []
        total_transaction = 0
        dt = 0
        async for x in stats:
            rd = x["latencyStats"]["reads"]
            read_latency.append(rd["latency"])
            total_read += rd["ops"]
            wr = x["latencyStats"]["writes"]
            write_latency.append(wr["latency"])
            total_write += wr["ops"]
            cmd = x["latencyStats"]["commands"]
            command_latency.append(cmd["latency"])
            total_command += cmd["ops"]
            ts = x["latencyStats"]["transactions"]
            transaction_latency.append(ts["latency"])
            total_transaction += ts["ops"]
            dt = x["localTime"]
        guild = self.bot.get_guild(self.GUILD_ID)
        ch = guild.get_channel(765818685922213948)  # type: ignore
        total_read = total_read or 1
        total_write = total_write or 1
        total_command = total_command or 1
        total_transaction = total_transaction or 1
        if ch is None:
            return await self.bot.send_owner(f"Your lxv channel is missing. Previously channel id {765818685922213948}")
        await ch.send(  # type: ignore
            f"# Data reporting\n"
            f"Read Latency: Average **{sum(read_latency)/(total_read*1000):.2f} ms** "
            f"in {total_read} operations\n"
            f"Write Latency: Average **{sum(write_latency)/(total_write*1000):.2f} ms** "
            f"in {total_write} operations\n"
            f"Command Latency: Average **{sum(command_latency)/(total_command*1000):.2f} ms** "
            f"in {total_command} operations\n"
            f"Transaction Latency: Average **{sum(transaction_latency)/(total_transaction*1000):.2f} ms**"
            f" in {total_transaction} operations\n"
            f"{discord.utils.format_dt(dt, 'F')}"  # type: ignore
        )

    @ping_lxv_db.before_loop
    async def check_connected(self):
        logger.info("PING DB: Waiting for bot...")
        await self.bot.wait_until_ready()

    @property
    def pet_query(self) -> dict:
        return {"_id": f"pet|{'|'.join(self.focus)}"}

    def is_mod(self, member: discord.Member) -> bool:
        if member.bot:
            return False
        if member.id in self.mod_cache:
            return True
        allowed = False
        if self.bot.owner.id == member.id or member.guild_permissions.administrator:
            allowed = True
            self.mod_cache.add(member.id)
        else:
            for r in member.roles:
                if r.id in self.mod_ids:
                    allowed = True
                    self.mod_cache.add(member.id)
                    break
        return allowed

    def mod_only(self, ctx) -> bool:
        return self.is_mod(ctx.author)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None or message.guild.id != self.GUILD_ID:
            return
        if message.author.bot:
            return
        if self.bot.TEST_MODE:
            return
        if "owo" in message.content.lower() or "uwu" in message.content.lower():
            setting = self.owo_drop_event_settings
            if not setting:
                return
            if not setting["enabled"]:
                return
            if str(message.author.id) in self._drop_cd:
                return
            self._drop_cd.add(str(message.author.id))
            chance = self.randgen.random()
            for i in range(5, 0, -1):
                if chance < setting[f"chance{i}"] / 100:
                    logger.info("Current Chance: %s%", chance * 100)
                    custom_embed = discord.Embed(
                        title=f"{self.item_render[self.gift_names[i-1]]} GIFTS {self.item_render[self.gift_names[i-1]]}",
                        description=f"{message.author.mention} got a **{self.gift_names[i-1]}**!",
                        color=discord.Colour.yellow(),
                    )
                    custom_embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar)
                    custom_embed.set_footer(text=f"Identifier id: Message {message.id}")
                    await message.reply(embed=custom_embed, mention_author=False)
                    exist = await self.LXV_COLLECTION.count_documents({"_id": f"inv{message.author.id}"}, limit=1)
                    if not exist:
                        await self.LXV_COLLECTION.insert_one({"_id": f"inv{message.author.id}", self.gift_names[i - 1]: 1})
                    else:
                        await self.LXV_COLLECTION.update_one(
                            {"_id": f"inv{message.author.id}"}, {"$inc": {self.gift_names[i - 1]: 1}}
                        )
                    break
                    # await message.reply("<a:gift3:1184120760374149201>")
            await asyncio.sleep(setting["cooldown"])
            self._drop_cd.remove(str(message.author.id))
        if (message.mentions and not self.mod_only(message)):
            for x in set(message.mentions):  # type: ignore
                x: discord.Member
                if self.is_mod(x):
                    await self.message_cache.add_message(message, f"ping-{message.id}")
                    break

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        if payload.guild_id != self.GUILD_ID:
            return
        message = await self.message_cache.remove_message(f"ping-{payload.message_id}")
        if message is None:
            return
        if self.bot.TEST_MODE:
            return

        # Do smth here
        # TODO: Maybe figure out how to consistently check who delete message?

        # Hardcoded channel id, will move the feature later
        await message.channel.send(f"{message.author.mention} Do not ghost ping <:smolaris:1155797791268937788>")
        guild = self.bot.get_guild(self.GUILD_ID)
        channel: discord.TextChannel
        channel = guild.get_channel(765818685922213948)  # type: ignore
        custom_embed = discord.Embed(
            title="Mod ping deleted", description=f"Message from **{message.author.mention}**", color=discord.Colour.random()
        )
        custom_embed.add_field(name="Original message", value=message.content)
        custom_embed.set_thumbnail(url=message.author.display_avatar)
        custom_embed.set_footer(text=f"UserId: {message.author.id} at #{message.channel.name} ")  # type: ignore
        await channel.send(embed=custom_embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if self.bot.TEST_MODE:
            return
        if (
            payload.guild_id == self.GUILD_ID
            and payload.emoji.name == '📝'
            and payload.channel_id in {self.lxv_link_channel, self.event_link_channel}
            and payload.message_id not in self.ignored
            and payload.user_id not in self.ignored
        ):
            guild = self.bot.get_guild(self.GUILD_ID) 
            if guild is None:
                guild = await self.bot.fetch_guild(self.GUILD_ID, with_counts=False)
            channel = guild.get_channel(payload.channel_id)
            if not isinstance(channel, discord.TextChannel):
                return
            message = await channel.fetch_message(payload.message_id)

            if message.author.id != self.bot.user.id:  # type: ignore
                self.ignored.add(payload.message_id)
                return

            member = guild.get_member(payload.user_id) 
            if member is None:  # Fallback
                member = await guild.fetch_member(payload.user_id)

            if member.bot:
                self.ignored.add(payload.user_id)
                return

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
        if (
            payload.guild_id == self.GUILD_ID
            and payload.emoji.id == 1046848826050359368
            and payload.message_id not in self.verified
            and payload.message_id not in self.ignored
            and payload.user_id not in self.ignored
            and (payload.user_id, payload.message_id) not in self.ignored
            and not self.event_disabled
        ):
            self.ignored.add(payload.user_id)

            guild = self.bot.get_guild(self.GUILD_ID)  
            if guild is None:  # Fallback
                guild = await self.bot.fetch_guild(self.GUILD_ID, with_counts=False)

            channel = guild.get_channel(payload.channel_id)
            if not isinstance(channel, discord.TextChannel):
                self.ignored.remove(payload.user_id)
                return
            
            try:
                message = await channel.fetch_message(payload.message_id)

                # Check if its from owo
                if message.author.id != 408785106942164992:
                    self.ignored.add(payload.message_id)
                    self.ignored.remove(payload.user_id)
                    return

                if not message.content and not message.embeds:
                    warning = await message.reply(
                        "WARNING: Content is empty. Retrying in 3 seconds " "<a:discordloading:792012369168957450>"
                    )
                    for i in range(3):
                        await asyncio.sleep(3)
                        message = await channel.fetch_message(payload.message_id)
                        await warning.edit(
                            content=f"WARNING: Content is empty. Retrying in 3 seconds "
                            f"<a:discordloading:792012369168957450> (Attempt {i+1})"
                        )
                        if message.content or message.embeds:
                            logger.warning("Attempted to get empty content. %s tries", i + 1)
                            await warning.delete()

                userid = str(payload.user_id)
                member = guild.get_member(payload.user_id) 
                if member is None:  # Fallback
                    member = await guild.fetch_member(payload.user_id)  

                if member.bot:
                    return

                if member.get_role(self.lxv_member_id) is None and self.lxv_only_event:
                    self.ignored.remove(payload.user_id)
                    return await message.add_reaction("<:joinlxv:1044554756569432094>")
                
                match_role = [
                    member.get_role(int(it)) if isinstance(it, str) else any([member.get_role(int(x)) for x in it])
                    for it in self.required_role_ids
                ]
                allowed = all(match_role)
                if not allowed:
                    arr = []
                    for i in range(len(self.required_role_ids)):
                        if match_role[i] is None:
                            role = guild.get_role(int(self.required_role_ids[i]))  # type: ignore
                            if role is None:
                                continue
                            arr.append(role.name)
                        elif not match_role[i]:
                            roles = [guild.get_role(int(x)) for x in self.required_role_ids[i]]  # type: ignore
                            if not any(roles):
                                continue
                            arr.append(roles)

                    # Failsafe if requirement role is non existent
                    if arr:
                        display = ""
                        for x in arr:
                            if isinstance(x, list):
                                display += "One of the following roles: " + ' '.join([y.mention for y in x]) + '\n'
                            else:
                                display += f"Required: {x.mention}\n"
                        custom_embed = discord.Embed(title="Missing roles", colour=discord.Colour.red(), description=display)
                        self.ignored.remove(payload.user_id)
                        return await message.reply(embed=custom_embed)
                link_channel = guild.get_channel(
                    self.lxv_link_channel if member.get_role(self.lxv_member_id) else self.event_link_channel
                )

                content = message.content if not message.embeds else message.embeds[0].description
                if content is None:
                    self.ignored.remove(payload.user_id)
                    return await message.reply("Invalid message type")

                if member.display_name not in content:
                    logger.error("Username Mismatch |Compare: %s | Content: %s", member.display_name, content)
                    self.ignored.add((payload.user_id, payload.message_id))
                    self.ignored.remove(payload.user_id)
                    return await message.reply(
                        "Username doesn't match/found in hunting message. " "If you believe this is yours, contact staff"
                    )
                """
                    Normal content would be
                    x | name hunt   [0]
                    y | caught pets [1]
                    z | team xp     [2]
                """
                check = content.lower().split('\n')
                counts = 0
                line_check = 0
                for i, line in enumerate(check):
                    for pet in self.focus:
                        counts += line.count(pet.lower())
                    if counts > 0:
                        line_check = i
                        break

                if counts == 0:
                    self.ignored.add((payload.user_id, payload.message_id))
                    self.ignored.remove(payload.user_id)
                    return await message.reply("No event pet found. If you believe there is event pet, contact staff")
                
                participants = {}
                detected = counts
                cursor = await self.LXV_COLLECTION.find_one(self.pet_query)
                if cursor:
                    participants = cursor["participants"]
                if userid in participants:
                    counts += participants[userid]
                participants.update({userid: counts})

                if self.bot.TEST_MODE:
                    self.verified.add(payload.message_id)
                    self.ignored.remove(payload.user_id)
                    return await message.reply("OK");

                link_embed = discord.Embed(title=member.name, description=content, color=discord.Colour.green())
                link_embed.add_field(
                    name="Detail",
                    value=f"Detected count: **{detected}**\n"
                    f"User id: {userid}\n"
                    f"Channel: {channel.mention}\n"
                    f"Jump url: [Link]({message.jump_url})\n"
                    f"Line: {line_check + 1}\n"
                    f"In case other wondering, "
                    f"react your event hunt message with <:newlxv:1046848826050359368>\n"
                    f"If anything wrong, for staff react the emoji below to edit",
                )
                link_embed.set_footer(text=f"Sent by: {member.display_name}")
                msg = await link_channel.send(embed=link_embed)  # type: ignore
                await msg.add_reaction('📝')

                if not cursor:
                    await self.LXV_COLLECTION.insert_one({"_id": f"pet|{'|'.join(self.focus)}", "participants": participants})
                else:
                    await self.LXV_COLLECTION.update_one(self.pet_query, {"$set": {"participants": participants}})

                self.verified.add(payload.message_id)
                verified = await self.LXV_COLLECTION.find_one({"_id": "verified_msg"})
                if not verified:
                    await self.LXV_COLLECTION.insert_one({"_id": "verified_msg", "msg_ids": list(self.verified)})
                else:
                    await self.LXV_COLLECTION.update_one({"_id": "verified_msg"}, {"$set": {"msg_ids": list(self.verified)}})

                await message.reply(f"Sent to {link_channel.mention}")  # type: ignore
                self.ignored.remove(payload.user_id)
            except Exception as e:
                await self.bot.send_error_to_owner(e, channel, None)
                if payload.user_id in self.ignored:
                    self.ignored.remove(payload.user_id)
                    
                if isinstance(e, KeyError):
                    return
                
                await message.reply("Something went wrong. Please try again later")
                if payload.message_id in self.verified:
                    self.verified.remove(payload.message_id)
            

    @commands.group(invoke_without_command=True, name="lxv")
    async def lxv_group(self, ctx: commands.Context):
        return await ctx.reply("?")
    
    @lxv_group.command(aliases=["owostats", "s"])
    async def owostat(self, ctx, member: discord.Member = None):  # type: ignore
        """
        Show owo stat (with *very new* haki db)
        """
        if member is None:
            member = ctx.author

        tz = pytz.timezone("US/Pacific")
        base_date =  datetime.datetime(2000, 1, 1).replace(
            hour=0, minute=0, second=0, microsecond=0, tzinfo=tz
        )
        date_now = datetime.datetime.now(datetime.timezone.utc).astimezone(tz)
        today_id = utils.date.absolute_day_diff(date_now, base_date)
        yesterday_id = utils.date.absolute_day_diff(utils.date.reset_tz(date_now - datetime.timedelta(days=1), tz), base_date)
        this_week_id = utils.date.absolute_day_diff(utils.date.reset_tz(date_now - datetime.timedelta(days=date_now.weekday()+1), tz), base_date)
        last_week_id = utils.date.absolute_day_diff(utils.date.reset_tz((date_now - datetime.timedelta(weeks=1, days=date_now.weekday()+1)), tz), base_date)
        this_month_id = utils.date.absolute_day_diff(utils.date.reset_tz(date_now.replace(day=1), tz), base_date)
        last_month_id = utils.date.absolute_day_diff(utils.date.reset_tz(utils.date.add_months(date_now, -1, 1), tz), base_date)
        this_year_id = utils.date.absolute_day_diff(utils.date.reset_tz(date_now.replace(month=1, day=1), tz), base_date)
        last_year_id = utils.date.absolute_day_diff(utils.date.reset_tz((date_now - datetime.timedelta(days=365)).replace(month=1, day=1), tz), base_date)

        query = {"$match": {"$and": [{"_id.user": member.id}, {"_id.dayId": {"$gte": 0}}]}}
        grouped_query = { 
            "$group": { 
                "_id": "$_id.user",
                "total": { "$sum": "$owoCount" },
                "today": { 
                    "$sum": { "$cond": [{ "$eq": ["$_id.dayId", today_id] }, "$owoCount", 0] }
                },
                "yesterday": { 
                    "$sum": { "$cond": [{ "$eq": ["$_id.dayId", yesterday_id] }, "$owoCount", 0] }
                },
                "this_week": { 
                    "$sum": { "$cond": [{ "$gte": ["$_id.dayId", this_week_id] }, "$owoCount", 0] }
                },
                "last_week": { 
                    "$sum": { "$cond": [{ "$and": [{ "$gte": ["$_id.dayId", last_week_id] }, { "$lt": ["$_id.dayId", this_week_id] }] }, "$owoCount", 0] }
                },
                "this_month": { 
                    "$sum": { "$cond": [{ "$gte": ["$_id.dayId", this_month_id] }, "$owoCount", 0] }
                },
                "last_month": { 
                    "$sum": { "$cond": [{ "$and": [{ "$gte": ["$_id.dayId", last_month_id] }, { "$lt": ["$_id.dayId", this_month_id] }] }, "$owoCount", 0] }
                },
                "this_year": { 
                    "$sum": { "$cond": [{ "$gte": ["$_id.dayId", this_year_id] }, "$owoCount", 0] }
                },
                "last_year": { 
                    "$sum": { "$cond": [{ "$and": [{ "$gte": ["$_id.dayId", last_year_id] }, { "$lt": ["$_id.dayId", this_year_id] }] }, "$owoCount", 0] }
                }
            }
        }

        if self._next_inactive_check is not None and self._next_inactive_check > date_now and member.get_role(self.lxv_member_id) is not None:
            start_check_id = utils.date.absolute_day_diff(utils.date.add_months(self._next_inactive_check, -self._inactive_interval_months, 1), base_date)
            grouped_query["$group"]["lxv"] = {
                "$sum": { "$cond": [{ "$gte": ["$_id.dayId", start_check_id] }, "$owoCount", 0] }
            }

        result = self.LXV_STAT_COLLECTION.aggregate([query, grouped_query])
        total = today = yesterday = this_week = last_week = this_month = last_month = this_year = last_year = 0
        lxv_req = -1;
        async for x in result:
            total = x["total"]
            today = x["today"]
            yesterday = x["yesterday"]
            this_week = x["this_week"]
            last_week = x["last_week"]
            this_month = x["this_month"]
            last_month = x["last_month"]
            this_year = x["this_year"]
            last_year = x["last_year"]
            if "lxv" in x:
                lxv_req = max(1000 - x["lxv"], 0)

        custom_embed = discord.Embed(color=discord.Colour.random())
        custom_embed.add_field(
            name="What is stat",
            value=f"Total: **{total}**\n"
            f"Today: **{today}**\n"
            f"Yesterday: **{yesterday}**\n",
            inline=False,
        )
        custom_embed.add_field(
            name="Not so accurate stat",
            value=f"This week: **{this_week}**\n"
            f"Last week: **{last_week}**\n"
            f"This month: **{this_month}**\n"
            f"Last month: **{last_month}**\n"
            f"This year: **{this_year}**\n"
            f"Last year: **{last_year}**\n",
            inline=False,
        )
        if lxv_req >= 0 and self._next_inactive_check is not None and self._next_inactive_check > date_now:
            custom_embed.add_field(
                name="Required LXV stat",
                value=f"**{lxv_req}** owos before check {discord.utils.format_dt(self._next_inactive_check, 'R')}\n" if lxv_req > 0 else f"You have reached requirement <a:kittyhyper:720191352259870750>. Next check {discord.utils.format_dt(self._next_inactive_check, 'R')}",
                inline=False,
            )
        custom_embed.set_author(name=member.name, icon_url=member.avatar)
        await ctx.send(embed=custom_embed)

    @lxv_group.group(invoke_without_command=True, aliases=["ev"], name="event")
    async def event_group(self, ctx: commands.Context):
        roles = [f"<@&{x}>" for x in self.required_role_ids if not isinstance(x, list)]
        optionaled = []
        for x in self.required_role_ids:
            if isinstance(x, list):
                optionaled.append(' '.join([f"<@&{y}>" for y in x]))
        custom_embed = discord.Embed(
            title="Super stat for event",
            description=f"Focused pet: `{'` `'.join(self.focus or ['None'])}`\n"
            f"Event counting "
            f"currently **{'disabled' if self.event_disabled else 'enabled'}**\n"
            f"LXV only event set to **{self.lxv_only_event}**\n",
            colour=discord.Colour.random(),
        )
        custom_embed.add_field(name="Required role", value=" ".join(roles), inline=False)
        custom_embed.add_field(name="One of the role", value="**->** " + '\n**->** '.join(optionaled), inline=False)
        await ctx.send(
            f"Hi event\n"
            f"For detail command, check from `s!help event` and `s!help event [command]` for detail\n"
            f"||Read the command detail before use 👀||\n"
            f"How to participate? If your hunt contains event pet, react with <:newlxv:1046848826050359368>",
            embed=custom_embed,
        )

    @event_group.command(name="focus", aliases=["f"])  # type: ignore
    async def focus_pet(self, ctx, *pet):
        """
        Set focus pet. For multiple pet just separate by space
        All verified **message id** posted at link channel will be cleared and event counting will set to enabled
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
        custom_embed = discord.Embed(
            title="Focus index",
            description=f"Are you sure want to focus to index `{'`, `'.join(res)}`?\n"
            f"**All verified message id posted at link will be cleared"
            f"and event counting will be set to enabled**",
            color=discord.Colour.green(),
        )
        confirm = ConfirmEmbed(ctx.author.id, custom_embed)
        await confirm.send(ctx)
        await confirm.wait()
        if not confirm.value:
            return
        self.focus = res
        self.verified = set()
        self.event_disabled = False
        await self.LXV_COLLECTION.update_one({"_id": "verified_msg"}, {"$set": {"msg_ids": []}})
        await self.LXV_COLLECTION.update_one(
            {"_id": "setting"}, {"$set": {"focus": list(res), "event_disabled": self.event_disabled}}
        )

    @event_group.command(aliases=["role"])
    async def setrole(self, ctx, roles: commands.Greedy[discord.Role], is_optional: bool = False):  # type: ignore
        if not self.mod_only(ctx):
            return await ctx.send("You are not allowed to use this command >:(")
        roles: List[discord.Role] = list(set(roles))
        custom_embed = discord.Embed(
            title="Set " + ("Optional Roles" if is_optional else "Roles"),
            description=f"Are you sure want to set role requirement "
            f"to {', '.join([r.mention for r in roles])}? If you set optional roles, the requirement roles will be **appended** instead of replaced",
            color=discord.Colour.green(),
        )
        confirm = ConfirmEmbed(ctx.author.id, custom_embed)
        await confirm.send(ctx)
        await confirm.wait()
        if not confirm.value:
            return
        res = [str(r.id) for r in roles]
        if is_optional:
            self.required_role_ids.append(res)
        else:
            self.required_role_ids = res  # type: ignore
        await self.LXV_COLLECTION.update_one({"_id": "setting"}, {"$set": {"required_role_ids": self.required_role_ids}})

    @event_group.command(aliases=['d', 'e', "enable", "disable"])
    async def toggle(self, ctx):
        """
        Toggle enable or disable event counting
        """
        if not self.mod_only(ctx):
            return await ctx.send("You are not allowed to use this command >:(")
        self.event_disabled = not self.event_disabled
        await self.LXV_COLLECTION.update_one({"_id": "setting"}, {"$set": {"event_disabled": self.event_disabled}})
        await ctx.send("Set to " + ("**disabled**" if self.event_disabled else "**enabled**"))

    @event_group.command(aliases=["lxv"])
    async def lxvonly(self, ctx):
        """
        Toggle enable or disable lxv event only
        """
        if not self.mod_only(ctx):
            return await ctx.send("You are not allowed to use this command >:(")
        self.lxv_only_event = not self.lxv_only_event
        await self.LXV_COLLECTION.update_one({"_id": "setting"}, {"$set": {"lxv_only_event": self.lxv_only_event}})
        await ctx.send(f"Set to **{self.lxv_only_event}**")

    @event_group.command(aliases=['s'])
    async def stat(self, ctx, user: Optional[discord.User] = None):
        """
        Show pet count
        """
        if user is None:
            user = ctx.author
        userid = str(user.id)  # type: ignore
        cursor = await self.LXV_COLLECTION.find_one(self.pet_query)
        if not self.focus:
            return await ctx.send("No focus pet currently")
        if not cursor:
            return await ctx.send("No pet index found")
        counts = cursor["participants"].get(userid, 0)
        await ctx.send(f"Total hunt: **{counts}**")

    @event_group.command(aliases=["lb"])
    async def leaderboard(self, ctx, length=5, page=1):
        """
        Show pet leaderboard
        """
        if not self.mod_only(ctx):
            return await ctx.send("You are not allowed to use this command >:(")
        if length < 1 or length > 25:
            return await ctx.send("Invalid number")
        if not self.focus:
            return await ctx.send("No focus pet currently. Please add by s!focus")
        cursor = await self.LXV_COLLECTION.find_one(self.pet_query)
        if not cursor:
            return await ctx.send("No leaderboard found")
        top = cursor["participants"]
        top = dict(sorted(top.items(), key=lambda it: it[1], reverse=True))
        custom_embed = discord.Embed(title=f"Leaderboard", color=discord.Colour.random())
        i = 1
        for userid, item in top.items():
            if i <= length * (page - 1):
                i += 1
                continue
            custom_embed.add_field(name=f"#{i}: {ctx.guild.get_member(int(userid))}", value=f"{item} Hunts", inline=False)
            i += 1
            if i > length * page:
                break
        await ctx.send(embed=custom_embed)

    @event_group.command()
    async def forcesend(self, ctx: commands.Context, member: discord.Member):
        """
        Force sending hunt message to channel. This only bypass username check
        """
        if not self.mod_only(ctx):
            return await ctx.send("You are not allowed to use this command >:(")
        if ctx.message.reference is None or not isinstance(ctx.message.reference.resolved, discord.Message):
            return await ctx.reply("Reply to OwO message then run this command again")
        if member.get_role(self.lxv_member_id) is None and self.lxv_only_event:
            return await ctx.reply("<:joinlxv:1044554756569432094>")

        message = ctx.message.reference.resolved
        link_channel = ctx.guild.get_channel(  # type: ignore
            self.lxv_link_channel if member.get_role(self.lxv_member_id) else self.event_link_channel
        )
        userid = str(member.id)

        content = message.content if not message.embeds else message.embeds[0].description
        if content is None:
            return await ctx.reply("Invalid message")
        """
            Normal content would be
            x | name hunt   [0]
            y | caught pets [1]
            z | team xp     [2]
            """
        check = content.split('\n')
        counts = 0
        line_check = 0
        for i, line in enumerate(check):
            for pet in self.focus:
                counts += line.count(pet.lower())
            if counts > 0:
                line_check = i
                break

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

        link_embed = discord.Embed(title=member.name, description=content, color=discord.Colour.green())
        link_embed.add_field(
            name="Detail",
            value=f"Detected count: **{detected}**\n"
            f"User id: {userid}\n"
            f"Channel: {ctx.channel.mention}\n"  # type: ignore
            f"Jump url: [Link]({message.jump_url})\n"
            f"Line: {line_check + 1}\n"
            f"In case other wondering, "
            f"react your event hunt message with <:newlxv:1046848826050359368>\n"
            f"If anything wrong, for staff react the emoji below"
        )
        link_embed.set_footer(text=f"Sent by: {member.display_name}")
        msg = await link_channel.send(embed=link_embed)  # type: ignore
        await msg.add_reaction('📝')

        if not cursor:
            await self.LXV_COLLECTION.insert_one({"_id": f"pet|{'|'.join(self.focus)}", "participants": participants})
        else:
            await self.LXV_COLLECTION.update_one(self.pet_query, {"$set": {"participants": participants}})

        self.verified.add(ctx.message.id)
        verified = await self.LXV_COLLECTION.find_one({"_id": "verified_msg"})
        if not verified:
            await self.LXV_COLLECTION.insert_one({"_id": "verified_msg", "msg_ids": list(self.verified)})
        else:
            await self.LXV_COLLECTION.update_one({"_id": "verified_msg"}, {"$set": {"msg_ids": list(self.verified)}})
        await ctx.reply(f"Sent to {link_channel.mention}")  # type: ignore

    @event_group.command(aliases=["acu"])
    async def addcountuser(self, ctx, user: discord.User, amount: int = 1):
        """
        Manual add count for user
        """
        if not self.mod_only(ctx):
            return await ctx.send("You are not allowed to use this command >:(")
        if amount < 0 or amount > 2147483647:
            return await ctx.send("Invalid number")
        cursor = await self.LXV_COLLECTION.find_one(self.pet_query)
        if not cursor:
            custom_embed = discord.Embed(
                title="Add count",
                description=f"Pet doesn't exist in database. " f"Do you want to add index of focus pet?",
                color=discord.Colour.green(),
            )
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

    @event_group.command(aliases=["sc"])
    async def setcount(self, ctx, user: discord.User, amount: int = 0):
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
        custom_embed = discord.Embed(
            title="Set count",
            description=f"You are changing pet count of user {user} "
            f"(Previous **{participants[userid]}**)\n"
            f"Proceed to continue?",
            color=discord.Colour.green(),
        )
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

    @lxv_group.command(aliases=["inv"])
    async def inventory(self, ctx: commands.Context):
        doc = await self.LXV_COLLECTION.find_one(f"inv{ctx.author.id}")
        if not doc:
            return await ctx.reply("Empty inventory")

        custom_embed = discord.Embed(color=discord.Colour.random())
        custom_embed.set_author(name=f"{ctx.author.name} - Inventory", icon_url=ctx.author.avatar)
        full_display = ""

        for k, v in doc.items():
            if k == "_id":
                continue
            full_display += f"{self.item_render[k]} **{k}**: {v}\n"
        custom_embed.add_field(name="Items", value=full_display)
        await ctx.send(embed=custom_embed)

    @lxv_group.group(invoke_without_command=True, name="owodropevent", aliases=["ode"])
    async def lxv_owo_drop_event(self, ctx: commands.Context):
        if not self.mod_only(ctx):
            return await ctx.reply("Womp")
        query = {"_id": "OwODropEvent"}
        guild_setting = await self.LXV_COLLECTION.find_one(query)
        if not guild_setting:
            guild_setting = {
                "_id": "OwODropEvent",
                "cooldown": 15.0,
                "chance1": 0.01,
                "chance2": 0.01,
                "chance3": 0.01,
                "chance4": 0.01,
                "chance5": 0.01,
                "enabled": False,
            }
            await self.LXV_COLLECTION.insert_one(guild_setting)
            self.owo_drop_event_settings = guild_setting
        custom_embed = discord.Embed(
            title="OwO Drop event setting",
            description=f"Cooldown: **{guild_setting['cooldown']} s**\n"
            f"Drop chance tier 1: **{guild_setting['chance1']}%**\n"
            f"Drop chance tier 2: **{guild_setting['chance2']}%**\n"
            f"Drop chance tier 3: **{guild_setting['chance3']}%**\n"
            f"Drop chance tier 4: **{guild_setting['chance4']}%**\n"
            f"Drop chance tier 5: **{guild_setting['chance5']}%**\n"
            f"Enabled: **{guild_setting['enabled']}**",
            color=discord.Colour.random(),
        )
        custom_embed.set_footer(text="Will enter cooldown state whether drop triggered or not")
        await ctx.send(embed=custom_embed)

    @lxv_owo_drop_event.command()
    async def set(self, ctx: commands.Context, setting: str, number: Optional[float] = None, state: Optional[bool] = None):
        mem: discord.Member = ctx.author  # type: ignore
        if not self.mod_only(ctx):
            return await ctx.reply("Womp womp")
        setting = setting.lower()
        if setting not in {"cooldown", "chance1", "chance2", "chance3", "chance4", "chance5", "enabled"}:
            return await ctx.reply("Not a valid event setting. Should be `cooldown`, `chance` or `enabled`")
        if (
            (number is None and state is None)
            or (setting != "enabled" and number is None)
            or (setting == "enabled" and number is not None)
        ):
            return await ctx.reply("Wer")
        query = {"_id": f"OwODropEvent"}
        guild_setting = await self.LXV_COLLECTION.find_one(query)
        if not guild_setting:
            default = {
                "_id": "OwODropEvent",
                "cooldown": 15.0,
                "chance1": 0.01,
                "chance2": 0.01,
                "chance3": 0.01,
                "chance4": 0.01,
                "chance5": 0.01,
                "enabled": False,
            }
            default[setting] = number if number is not None else state
            await self.LXV_COLLECTION.insert_one(default)
            self.owo_drop_event_settings = default
        else:
            await self.LXV_COLLECTION.update_one(query, {"$set": {setting: number if number is not None else state}})
            guild_setting[setting] = number if number is not None else state
            self.owo_drop_event_settings = guild_setting
        await ctx.send(f"Successfully set **{setting}** to **{number if number is not None else state}**")

    @lxv_group.group(name="automember", aliases=["am"], invoke_without_command=True)
    async def auto_member(self, ctx: commands.Context):
        if not self.mod_only(ctx):
            return await ctx.send("You are not allowed to use this command >:(")
        doc = await self.LXV_COLLECTION.find_one({"_id": "autoMember"})
        if not doc or "nextTime" not in doc or "repeatEvery" not in doc or "disabled" not in doc:
            return await ctx.reply("No setting found")
        display_date = discord.utils.format_dt(self._last_inactive_check, 'R') if self._last_inactive_check else "Not yet"
        custom_embed = discord.Embed(
            title="Not so informative auto check member role",
            description=f"Last check: {display_date}\n"
            f"Next schedule: {discord.utils.format_dt(doc['nextTime'], 'R')}\n"
            f"Repeat schedule every: **{doc['repeatEvery']} months**\n"
            f"Running: **{self.auto_remove_member.is_running()}**\n"
            f"Disabled: **{doc['disabled']}**\n"
            f"||For more info, please check by running command `s!help lovesick automember`||",
            color=discord.Colour.random(),
        )
        await ctx.send(embed=custom_embed)

    @auto_member.command(name="memberinfo", aliases=["mi"])
    async def member_info(self, ctx: commands.Context):
        if not self.mod_only(ctx):
            return await ctx.send("You are not allowed to use this command >:(")
        if not self._inactives_member_data:
            if not self._last_inactive_check:
                return await ctx.reply("Not yet")
            return await ctx.reply("No inactive member")
        display_date = discord.utils.format_dt(self._last_inactive_check) if self._last_inactive_check else ''
        menu = SimplePages(DataEmbedSource(self._inactives_member_data, 15, f"Inactive members as of {display_date}", lambda idx, x: f"{x['name']} [{x['id']}] - **{x['count']}**"))
        await menu.start(ctx)

    @auto_member.command(name="startschedule", aliases=["ss"])
    async def start_shedule(self, ctx: commands.Context, repeat_time: int = 2, start_time: Optional[int] = None):
        """
        Start / Restart schedule for auto member removal.
        Set repeat_time for repeat schedule in months. Default 2 months
        Set start_time for starting first schedule in days. Default repeat time. Set 0 to immediately execute first schedule
        """
        if not self.mod_only(ctx):
            return await ctx.send("You are not allowed to use this command >:(")
        if repeat_time < 1:
            return await ctx.send("Invalid time. Must be greater than 0 days")
        if start_time is None:
            start_time = repeat_time
        if start_time < 0:
            return await ctx.send("Invalid start time")

        tz = pytz.timezone("US/Pacific")
        current_time = discord.utils.snowflake_time(ctx.message.id).astimezone(tz)
        next_time = utils.start_of_day(utils.date.add_months(current_time, start_time, 1))
        custom_embed = discord.Embed(
            title="Start schedule",
            description=f"Schedule for auto check inactive lovesick member will be set to **every {repeat_time} month(s)** starting **{start_time} month(s) from now** {discord.utils.format_dt(next_time, 'R')}.\n"
            f"This also enable the schedule (if previously disabled). Are you sure?",
            color=discord.Colour.green(),
        )
        confirm = ConfirmEmbed(ctx.author.id, custom_embed)
        await confirm.send(ctx)
        await confirm.wait()
        if not confirm.value:
            return
        exists = await self.LXV_COLLECTION.count_documents({"_id": "autoMember"}, limit=1)
        if not exists:
            await self.LXV_COLLECTION.insert_one(
                {"_id": "autoMember", "repeatEvery": repeat_time, "nextTime": next_time, "disabled": False}
            )
        else:
            await self.LXV_COLLECTION.update_one(
                {"_id": "autoMember"}, {"$set": {"repeatEvery": repeat_time, "nextTime": next_time, "disabled": False}}
            )
        if self.auto_remove_member.is_running():
            self.auto_remove_member.restart()
        else:
            self.auto_remove_member.start()

    @auto_member.command(name="cancelschedule", aliases=["cs"])
    async def cancel_shedule(self, ctx: commands.Context):
        """
        Cancel schedule duh
        """
        if not self.mod_only(ctx):
            return await ctx.send("You are not allowed to use this command >:(")
        exists = await self.LXV_COLLECTION.count_documents({"_id": "autoMember"}, limit=1)
        if not exists:
            return await ctx.reply("No schedule running")
        custom_embed = discord.Embed(
            title="Cancel schedule",
            description=f"Are you sure???",
            color=discord.Colour.red(),
        )
        confirm = ConfirmEmbed(ctx.author.id, custom_embed)
        await confirm.send(ctx)
        await confirm.wait()
        if not confirm.value:
            return
        await self.LXV_COLLECTION.update_one({"_id": "autoMember"}, {"$set": {"disabled": True}})
        if self.auto_remove_member.is_running():
            self.auto_remove_member.cancel()

    @auto_member.command(name="rebootchedule", aliases=["rs"])
    async def reboot_schedule(self, ctx: commands.Context, restart=True):
        """
        Restart / Resume schedule
        """
        if not self.mod_only(ctx):
            return await ctx.send("You are not allowed to use this command >:(")
        doc = await self.LXV_COLLECTION.find_one({"_id": "autoMember"})
        tz = pytz.timezone("US/Pacific")
        if not doc:
            return await ctx.reply("No schedule running")
        if restart:
            current_time = discord.utils.snowflake_time(ctx.message.id).astimezone(tz)
            next_time = utils.date.reset_tz(utils.date.add_months(current_time, doc["repeatEvery"], 1), tz)
            await self.LXV_COLLECTION.update_one({"_id": "autoMember"}, {"$set": {"nextTime": next_time, "disabled": False}})
        else:
            await self.LXV_COLLECTION.update_one({"_id": "autoMember"}, {"$set": {"disabled": False}})

        if self.auto_remove_member.is_running():
            self.auto_remove_member.restart()
        else:
            self.auto_remove_member.start()

        return await ctx.reply("Restarting schedule" if restart else "Resuming schedule")

    @auto_member.command(name="settimer", aliases=["st"])
    async def set_timer(self, ctx: commands.Context, start_after: int = 2):
        """
        Set the timer for next schedule in months
        Set to 0 to immediately execute
        """
        if not self.mod_only(ctx):
            return await ctx.send("You are not allowed to use this command >:(")
        doc = await self.LXV_COLLECTION.find_one({"_id": "autoMember"})
        tz = pytz.timezone("US/Pacific")
        if not doc:
            return await ctx.reply("No schedule running")
        if start_after < 0:
            return await ctx.reply("Invalid month")
        current_time = discord.utils.snowflake_time(ctx.message.id).astimezone(tz)
        next_time = utils.date.reset_tz(utils.date.add_months(current_time, start_after, 1), tz)
        custom_embed = discord.Embed(
            title="Set Timer",
            description=f"Next schedule for auto check inactive lovesick member will set to **{start_after} months** {discord.utils.format_dt(next_time, 'R')} (previously {discord.utils.format_dt(doc['nextTime'], 'R')})",
            color=discord.Colour.green(),
        )
        confirm = ConfirmEmbed(ctx.author.id, custom_embed)
        await confirm.send(ctx)
        await confirm.wait()
        if not confirm.value:
            return
        await self.LXV_COLLECTION.update_one({"_id": "autoMember"}, {"$set": {"nextTime": next_time}})
        if self.auto_remove_member.is_running():
            self.auto_remove_member.restart()

    @auto_member.command()
    async def execute(self, ctx: commands.Context):
        if not self.mod_only(ctx):
            return await ctx.send("You are not allowed to use this command >:(")
        if not ctx.author.guild_permissions.manage_roles and self.bot.owner.id != ctx.author.id:  # type: ignore
            return await ctx.send("Manage role required")
        if not self._inactives_member_data:
            return await ctx.reply("Not yet")
        custom_embed = discord.Embed(
            title="Execute auto remove member role",
            description=f"This will remove role from member in previous checked list (you can see the list from command `s!lxv automember memberinfo`)\n"
            f"**This action is irreversible!**. Are you sure?",
            color=discord.Colour.red(),
        )
        confirm = ConfirmEmbed(ctx.author.id, custom_embed)
        await confirm.send(ctx)
        await confirm.wait()
        if not confirm.value:
            return
        lxv_role = ctx.guild.get_role(self.lxv_member_id)  # type: ignore
        if lxv_role is None:
            return await ctx.reply("Lxv member role missing")
        msg = await ctx.send("Loading <a:discordloading:792012369168957450>")
        for data in self._inactives_member_data:
            member = ctx.guild.get_member(data["id"])  # type: ignore
            if member is None:
                continue
            await member.remove_roles(lxv_role, reason="Inactive member with less than 1000 owos")
        await msg.edit(content="Remove done!")

    @auto_member.command()
    async def undo(self, ctx: commands.Context):
        if not self.mod_only(ctx):
            return await ctx.send("You are not allowed to use this command >:(")
        if not ctx.author.guild_permissions.manage_roles and self.bot.owner.id != ctx.author.id:  # type: ignore
            return await ctx.send("Manage role required")
        if not self._inactives_member_data:
            return await ctx.reply("Not yet")
        custom_embed = discord.Embed(
            title="Undo remove member role",
            description=f"This will give role in member in previous checked list (you can see the list from command `s!lxv automember memberinfo`)\n"
            f"**This action is irreversible!**. Are you sure?",
            color=discord.Colour.red(),
        )
        confirm = ConfirmEmbed(ctx.author.id, custom_embed)
        await confirm.send(ctx)
        await confirm.wait()
        if not confirm.value:
            return
        lxv_role = ctx.guild.get_role(self.lxv_member_id)  # type: ignore
        if lxv_role is None:
            return await ctx.reply("Lxv member role missing")
        msg = await ctx.send("Loading <a:discordloading:792012369168957450>")
        for data in self._inactives_member_data:
            member = ctx.guild.get_member(data["id"]) # type: ignore
            if member is None:
                continue
            await member.add_roles(lxv_role, reason="Undo execute remove role")
        await msg.edit(content="Undo done!")

    @auto_member.command()
    async def forcecheck(self, ctx: commands.Context):
        """
        Force check by given interval [WIP]
        """
        # TODO: Implement force check using UI
        if not self.mod_only(ctx):
            return await ctx.send("You are not allowed to use this command >:(")
        doc = await self.LXV_COLLECTION.find_one({"_id": "autoMember"})
        if not doc:
            return await ctx.reply("No schedule running")

        await ctx.reply("WIP")
async def setup(bot: SewentyBot):
    await bot.add_cog(LoveSick(bot))
