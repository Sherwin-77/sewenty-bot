from __future__ import annotations

import discord
from discord.ext import commands
import pytz

import asyncio
import calendar
from datetime import datetime
import datetime as dt
from io import BytesIO
import random
from traceback import format_exception
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from main import SewentyBot


class ConversionFailed(BaseException):
    pass


class TacoNode:
    def __init__(self, cost: int, boost: int, level: int, max_level: int):
        self.level = int(level)
        self.boost = int(boost)
        self.max_level = int(max_level)
        self.base_cost = int(cost) / (level + 1)**2

    @classmethod
    def from_dict(cls, to_convert: dict) -> TacoNode:
        """
        Convert from dict to TacoNode

        Parameters
        ----------
        to_convert : dict
        Dict to convert

        Returns
        -------
        TacoNode
        """
        try:
            level = to_convert["level"]
            max_level = to_convert["max_level"]
            boost = to_convert["boost"]
            base_cost = to_convert["base_cost"]
        except KeyError:
            raise ConversionFailed("Invalid dict key")
        build = cls(0, 0, 0, 0)
        build.level = level
        build.max_level = max_level
        build.boost = boost
        build.base_cost = base_cost
        return build

    @property
    def cost(self) -> float:
        return self.base_cost * (self.level + 1) ** 2

    @property
    def value(self) -> float:
        if self.cost == 0:
            return 0.0
        return self.boost/self.cost

    @property
    def dict(self) -> dict:
        return {"level": self.level,
                "max_level": self.max_level,
                "boost": self.boost,
                "base_cost": self.base_cost}

    def upgrade(self):
        """
        Simulate upgrade on taco, updating level and cost
        """
        if self.level >= self.max_level:
            raise ValueError("Maxed level")
        self.level += 1
        if self.level == self.max_level:
            self.base_cost = 0
            self.boost = 0

    def __repr__(self):
        return f"<TacoNode object base_cost={self.base_cost} boost={self.boost} max_level={self.max_level}>"

    def __str__(self):
        return self.__repr__()


class Taco(commands.Cog):
    def __init__(self, bot: SewentyBot):
        self.bot: SewentyBot = bot
        self.COLLECTION = self.bot.DB["userdata"]

        # This may be changed as soon as new location is confirmed
        self.REGISTERED_LOCATION = {"beach", "city", "mall"}
        self.REGISTERED_ETC = {"Taco Truck Upgrades 🚚": "",
                               "Ice Cream Stand Upgrades 🍦": "beach",
                               "Hotdog Cart Upgrades 🌭": "city",
                               "Mall Kiosk Upgrades 🛒": "mall"}
        self.SHORTCUT_LOCATION = {'s': '', 'b': "beach", "c": "city", "shack": '', 'm': "mall"}
        self.HIRE = {"Apprentice", "Cook", "Advertiser", "Greeter", "Sous", "Head", "Executive",
                     "Cashier", "Associate", "Janitor", "Security", "Sales", "Leader", "Manager"}
        self.STOP_CLAUSE = {"exit", "quit", "abort", 'q', "done", "end"}
        self.taco_set, self.taco_recommend = set(), set()
        self.using_auto = set()

    async def read_taco(self, ctx: commands.Context, embed: discord.Embed,
                        location_locked: Optional[str] = None) -> Optional[tuple[str, dict, dict]]:

        """
        Get taco upgrade from embed. Returns None if error happened or not matching location_locked
        """
        try:
            new = embed.description.split('\n')  # type: ignore
            title = embed.title.split("| ")[-1]  # type: ignore
            is_shack = False
            if "Shack" in title:
                is_shack = True
            title = self.REGISTERED_ETC[title] if title in self.REGISTERED_ETC else title.split(" ")[0].lower()
        except (KeyError, AttributeError):
            return None

        location = title if title in self.REGISTERED_LOCATION else ""

        if is_shack and not location:
            await ctx.send("New location detected and unregistered. Please DM invalid-user#8807")
            return None

        if location_locked is not None and location != location_locked and (location_locked != "shack" or is_shack):
            await ctx.send("Invalid location >:(")
            return None

        to_update = {}
        taco_data = {}
        for j in range(len(new) - 1):
            # cursor selecting the name
            if '(' not in new[j]:
                continue
            if '✅' in new[j]:
                to_update.update({new[j + 2].split('`')[1].capitalize(): 0})
                taco_data.update({new[j + 2].split('`')[1].capitalize(): TacoNode(0, 0, 0, 0)})
                continue
            if "+$" not in new[j + 2]:
                continue
            level_range = new[j].split('`')[1].removeprefix('(').removesuffix(')').split('/')
            boost = int(new[j + 2].split("/hr")[0].split('$')[-1])
            cost = int(new[j + 1].split('$')[-1].replace(',', ''))
            id_ = new[j + 3].split('`')[-2].capitalize()
            to_update.update({id_: boost / cost})
            taco_data.update({id_: TacoNode(cost=cost,
                                            boost=boost,
                                            level=int(level_range[0]),
                                            max_level=int(level_range[-1]))})
        data_id = f"{ctx.author.id}taco{location}"
        return data_id, to_update, taco_data

    async def update_taco(self, taco: dict, taco_data: dict) -> None:
        """
        Update taco and taco_data. Only accept dict format {_id: upgrade}

        Parameters
        ----------
        taco : dict
        taco_data : dict

        Returns
        -------
        None
        """

        for k in taco.keys():
            query = {"_id": k}
            counts = await self.COLLECTION.count_documents(query)
            converted = {}
            if len(taco_data) > 0:
                converted = {key: node.dict for key, node in taco_data[k].items()}
            if counts == 0:
                await self.COLLECTION.insert_one({"_id": k, "taco": taco[k], "taco_data": converted})
            else:
                cursor = await self.COLLECTION.find_one(query)
                old_update = cursor["taco"]
                old_taco_data = dict()
                if "taco_data" in cursor:
                    old_taco_data = cursor["taco_data"]
                merged = {**old_update, **taco[k]}
                data_merged = {**old_taco_data, **converted}
                await self.COLLECTION.update_one(query, {"$set": {"taco": merged, "taco_data": data_merged}})

    @commands.command(name="tacoset", aliases=["ts"])
    async def set_taco(self, ctx: commands.Context, multiple: bool = False):
        """
        Set your taco value based on embed
        Detect up to 5 message if not multiple else 8
        To set multiple: s!tacoset true
        """
        if str(ctx.author.id) in self.taco_set:
            await ctx.send('Chill down <:blobsob:809721186966831105>', delete_after=2)
            return
        history = [x async for x in ctx.channel.history(limit=5 if not multiple else 8)]
        placeholder = dict()
        data_placeholder = dict()
        for i in history:
            if i.author.id != 490707751832649738:
                continue
            embed = i.embeds
            if len(embed) < 1:
                continue
            res = await self.read_taco(ctx, embed[-1])
            if res is None:
                continue
            data_id, to_update, taco_data = res

            if data_id not in placeholder:
                placeholder.update({data_id: to_update})
            else:
                val = placeholder[data_id]
                placeholder.update({data_id: {**val, **to_update}})

            if data_id not in data_placeholder:
                data_placeholder.update({data_id: taco_data})
            else:
                data_val = data_placeholder[data_id]
                data_placeholder.update({data_id: {**data_val, **taco_data}})

            if not multiple:
                break

        if len(placeholder) < 1:
            return await ctx.reply("No embed detected", mention_author=False)
        await self.update_taco(placeholder, data_placeholder)
        await ctx.message.add_reaction('👍')

        if multiple:
            def check(reaction, users):
                return users == ctx.author and str(reaction.emoji) == "❗" and reaction.message == ctx.message

            await ctx.message.add_reaction("❗")
            try:
                await self.bot.wait_for("reaction_add", timeout=30, check=check)
            except asyncio.TimeoutError:
                return
            await ctx.send("Multiple check feature look up to **8 messages** before you and it **overrides** "
                           "older embed if newer one is the same so be careful")
        self.taco_set.add(str(ctx.author.id))
        await asyncio.sleep(2)
        self.taco_set.remove(str(ctx.author.id))

    @commands.command(name='tacorecommend', aliases=['tr'])
    async def recommend_taco(self, ctx,  location: str = "", auto_update=False):
        """
        Recommend upgrade. For specific location e.g. beach:
        s!tacorecommend beach
        """

        location = location.lower()
        location = location if location not in self.SHORTCUT_LOCATION else self.SHORTCUT_LOCATION[location]
        if location not in self.REGISTERED_LOCATION and location:
            return await ctx.send("You input scary location to me <:blobsob:809721186966831105>", delete_after=5)
        if str(ctx.author.id) in self.taco_recommend:
            return await ctx.send("Chill down <:blobsob:809721186966831105>", delete_after=4)

        def valid_number(msg: discord.Message) -> bool:
            if msg.channel.id != ctx.channel.id or msg.author.id != ctx.author.id:
                return False
            if not msg.content.isdecimal():
                return False
            if int(msg.content) < 1:
                return False
            return True

        query = {"_id": f"{ctx.author.id}taco{location}"}
        counts = await self.COLLECTION.count_documents(query)
        if counts == 0:
            return await ctx.reply("Give taco stat when <:PaulOwO:721154434297757727>",
                                   mention_author=False,
                                   delete_after=5)
        cursor = await self.COLLECTION.find_one(query)
        if "taco_data" not in cursor:
            return await ctx.send("New taco data needed. Please update it")

        taco_data = cursor["taco_data"]
        taco_data = {key: TacoNode.from_dict(value) for key, value in taco_data.items()}
        taco = cursor["taco"]
        await ctx.send(f"Input your budget for location **{location}**. INFO: auto_update set to {auto_update}\n"
                       f"auto_update decide whether your recommendation will be saved in database or not")
        try:
            budget = await self.bot.wait_for("message", check=valid_number, timeout=60.0)
        except asyncio.TimeoutError:
            return await ctx.send("No response in 1 minute. Aborting")

        budget = int(budget.content)
        bought = {}
        cost = 0
        while cost <= budget:
            t = max(taco, key=taco.get)  # type: ignore
            if taco[t] == 0:
                await ctx.send("Upgrade maxed")
                break
            if t not in taco_data:
                return await ctx.send(f"**Error!** Please update the following upgrade: {t}")
            selected: TacoNode = taco_data[t]
            if cost + selected.cost > budget:
                break

            cost += selected.cost
            selected.upgrade()
            taco = {k: v.value for k, v in taco_data.items()}
            if t not in bought:
                bought.update({t: 1})
            else:
                bought[t] += 1

        custom_embed = discord.Embed(description="", color=discord.Colour.random())
        for k in sorted(bought):
            v = bought[k]
            action = "hire" if k in self.HIRE else "buy"
            custom_embed.description += f"{action} {k} ({v} times)\n"  # type: ignore
        custom_embed.set_footer(text=f"Used {int(cost)} total of {budget} budget")
        if auto_update:
            await self.update_taco({query: taco}, {query: taco_data})  # type: ignore
        await ctx.send(embed=custom_embed)
        self.taco_recommend.add(str(ctx.author.id))
        await asyncio.sleep(4)
        self.taco_recommend.remove(str(ctx.author.id))

    @commands.command(name="tscleartruck", aliases=['tct'])
    async def delete_truck(self, ctx):
        if str(ctx.author.id) in self.taco_set:
            await ctx.send("Chill down <:blobsob:809721186966831105>", delete_after=2)
            return
        dl = ["Register", "Assistant", "Driver", "Kitchen", "Engine"]
        query = {"_id": f"{ctx.author.id}taco"}
        counts = await self.COLLECTION.count_documents(query)
        if counts == 0:
            await ctx.reply("Your data not exist <:PaulOwO:721154434297757727>", mention_author=False, delete_after=5)
        else:
            cursor = await self.COLLECTION.find_one(query)
            taco = cursor["taco"]
            taco_data = {}
            if "taco_data" in cursor:
                taco_data = cursor["taco_data"]
            for x in dl:
                taco.pop(x)
                taco_data.pop(x)
            await self.COLLECTION.update_one(query, {"$set": {"taco": taco, "taco_data": taco_data}})
            await ctx.message.add_reaction('👍')
        self.taco_set.add(str(ctx.author.id))
        await asyncio.sleep(2)
        self.taco_set.remove(str(ctx.author.id))

    @commands.command(name="tsclearstand", aliases=['tcs'])
    async def delete_stand(self, ctx):
        if str(ctx.author.id) in self.taco_set:
            await ctx.send("Chill down <:blobsob:809721186966831105>", delete_after=2)
            return
        dl = ["Decals", "Wheels", "Mixers", "Server", "Freezer"]
        query = {"_id": f"{ctx.author.id}tacobeach"}
        counts = await self.COLLECTION.count_documents(query)
        if counts == 0:
            await ctx.reply("Your data not exist <:PaulOwO:721154434297757727>", mention_author=False,
                            delete_after=5)
        else:
            cursor = await self.COLLECTION.find_one(query)
            taco = cursor["taco"]
            taco_data = {}
            if "taco_data" in cursor:
                taco_data = cursor["taco_data"]
            for x in dl:
                taco.pop(x)
                taco_data.pop(x)
            await self.COLLECTION.update_one(query, {"$set": {"taco": taco, "taco_data": taco_data}})
        self.taco_set.add(str(ctx.author.id))
        await asyncio.sleep(2)
        self.taco_set.remove(str(ctx.author.id))

    @commands.command(name="tsclearcart", aliases=['tcc'])
    async def delete_cart(self, ctx):
        if str(ctx.author.id) in self.taco_set:
            await ctx.send("Chill down <:blobsob:809721186966831105>", delete_after=2)
            return
        dl = ["Buns", "Condiments", "Beverages", "Coolers", "Grill"]
        query = {"_id": f"{ctx.author.id}tacocity"}
        counts = await self.COLLECTION.count_documents(query)
        if counts == 0:
            await ctx.reply("Your data not exist <:PaulOwO:721154434297757727>", mention_author=False,
                            delete_after=5)
        else:
            cursor = await self.COLLECTION.find_one(query)
            taco = cursor["taco"]
            taco_data = {}
            if "taco_data" in cursor:
                taco_data = cursor["taco_data"]
            for x in dl:
                taco.pop(x)
                taco_data.pop(x)
            await self.COLLECTION.update_one(query, {"$set": {"taco": taco, "taco_data": taco_data}})
            await ctx.message.add_reaction('👍')
        self.taco_set.add(str(ctx.author.id))
        await asyncio.sleep(2)
        self.taco_set.remove(str(ctx.author.id))

    @commands.command(name="tsgo")
    async def auto_taco(self, ctx: commands.Context, location: str):
        """
        Automate your taco upgrade
        """

        if ctx.author.id in self.using_auto:
            return await ctx.reply("Please complete your previous auto taco before using new one")
        self.using_auto.add(ctx.author.id)
        location = location.lower()
        location = location if location in self.REGISTERED_LOCATION else "shack"
        await ctx.send(f"Starting helper in location: **{location}**\n"
                       f"To exit helper just type 'exit'")

        def valid_answer(msg) -> bool:
            expected_answer = {'y', 'n', "yes", "no"}
            expected_answer |= self.STOP_CLAUSE
            if msg.channel.id != ctx.channel.id or msg.author.id != ctx.author.id:
                return False
            if msg.content.lower() not in expected_answer:
                return False
            return True

        def valid_taco(msg: discord.Message) -> bool:
            if(
                    msg.channel.id == ctx.channel.id and
                    msg.author.id == ctx.author.id and
                    msg.content.lower() in self.STOP_CLAUSE
            ):
                return True

            if msg.channel.id != ctx.channel.id or msg.author.id != 490707751832649738:
                return False

            if len(msg.embeds) < 1 and msg.interaction is not None and msg.interaction.user.id == ctx.author.id:
                return True

            if len(msg.embeds) < 1:
                return False

            return True

        async def get_answer() -> Optional[bool]:
            """
            Get user input. Returns None if user want to exit
            """
            temp = False
            while not temp:
                temp = await self.bot.wait_for("message", check=valid_answer, timeout=60.0)
            if temp.content.lower() in self.STOP_CLAUSE:
                return None
            if temp.content.lower() in {'y', "yes"}:
                return True
            return False

        is_updating = False
        taco = {}
        taco_data = {}
        query = {"_id": f"{ctx.author.id}taco{location if location != 'shack' else ''}"}
        try:
            await ctx.send("Do you want to update your upgrade first? (y/n)\n"
                           "**Warning:** Starting from <t:1658728800:D>, you need to update all the upgrade"
                           " as we updated ~~privacy policy~~ how the command work\n"
                           "TL;DR: Just say y")
            state = await get_answer()
            if state is None:
                self.using_auto.remove(ctx.author.id)
                return await ctx.send("Aborting..")
            if state:
                is_updating = True
        except asyncio.TimeoutError:
            return await ctx.send("No answer in 1 minute. Aborting")

        try:
            success: bool = False
            while is_updating:
                if success:
                    await ctx.send("**✅ Taco data merged**. Continue do your taco\n"
                                   "Type 'done' if you're done")
                else:
                    await ctx.send("Do your taco here /upgrades, /decorations or anything)\n"
                                   "Type 'done' if you're done")
                message = await self.bot.wait_for("message", check=valid_taco, timeout=60.0)
                if message.content.lower() in self.STOP_CLAUSE:
                    break
                await asyncio.sleep(0.5)
                if len(message.embeds) < 1:
                    success = False
                    continue
                res = await self.read_taco(ctx, message.embeds[0], location_locked=location)
                if res is None:
                    success = False
                    continue

                # returns upgrade only
                data_id, placeholder, data_placeholder = res

                taco = {**taco, **placeholder}
                taco_data = {**taco_data, **data_placeholder}
                success = True

            m = await ctx.send("Processing data <a:discordloading:792012369168957450>")
            assert query["_id"] not in taco and query["_id"] not in taco_data

            counts = await self.COLLECTION.count_documents(query)
            if counts < 1 and len(taco) < 1:
                self.using_auto.remove(ctx.author.id)
                return await m.edit(content="No data to recommend")
            if counts > 0:
                cursor = await self.COLLECTION.find_one(query)
                # old one returns upgrade only
                old_update = cursor["taco"]
                old_taco_data = dict()
                if "taco_data" in cursor:
                    old_taco_data = cursor["taco_data"]
                    old_taco_data = {key: TacoNode.from_dict(value) for key, value in old_taco_data.items()}

                taco = {**old_update, **taco}
                taco_data = {**old_taco_data, **taco_data}

            await m.edit(content="Done! Follow the upgrade below\n"
                                 "**Type 'abort' when you're done**")
            custom_embed = discord.Embed(color=discord.Colour.random())
            # loop recommendation until done
            while True:
                abort = False
                if len(taco) < 1:
                    await ctx.send("No more data to recommend. Aborting")
                    break
                t = max(taco, key=taco.get)  # type: ignore
                v = format(taco[t], '.3e')
                if taco[t] == 0:
                    await ctx.send(f"Upgrade already maxed. Aborting")
                    break
                if t not in taco_data:
                    await ctx.send(f"**Error!** Please update following upgrade: {t}\n"
                                   f"Aborting..")
                    break
                action = "hire" if t in self.HIRE else "buy"

                custom_embed.description = f"/{action} id: {t.lower()}"
                custom_embed.set_footer(text=f"Effectiveness: {v} | 'abort' if you're done")
                await ctx.send(embed=custom_embed)

                while True:
                    message: discord.Message = await self.bot.wait_for("message", check=valid_taco, timeout=90.0)
                    if message.content.lower() in self.STOP_CLAUSE:
                        abort = True
                        break
                    await asyncio.sleep(1)
                    if len(message.embeds) < 1:
                        await ctx.send("No embed", delete_after=3)
                        continue

                    if message.embeds[0] is None or message.embeds[0].description is None:
                        continue

                    # check interaction origin
                    if message.interaction is None and t.lower() in message.embeds[0].description.lower():
                        await ctx.send("Looks like this isn't from slash command. We will accept this nevertheless")
                    elif message.interaction is None:
                        continue
                    if message.interaction is not None:
                        interaction = message.interaction
                        if interaction.user.id != ctx.author.id or interaction.name not in {"buy", "hire"}:
                            continue
                        if interaction.name == "hire" and "you have hired" not in message.embeds[0].description.lower():
                            continue
                        if '❌' in message.embeds[0].description.lower():
                            continue
                        if "don't have enough money!" in message.embeds[0].description.lower():
                            await ctx.send("Looks like you don't have enough money. Aborting...")
                            abort = True
                            break
                        if t.lower() not in message.embeds[0].description.lower():
                            await ctx.send("You bought wrong upgrade. It won't be detected until you update with s!ts")
                            continue
                    # noinspection PyTypeChecker
                    selected: TacoNode = taco_data[t]
                    if selected.level < selected.max_level:
                        selected.upgrade()
                        taco = {k: v.value for k, v in taco_data.items()}
                    break

                if abort:
                    break

            self.using_auto.remove(ctx.author.id)
            await self.update_taco({query["_id"]: taco}, {query["_id"]: taco_data})
            return await ctx.send("Updated your taco data\n"
                                  "**Set your upgrade** if you bought upgrade but not enough money")

        except asyncio.TimeoutError:
            self.using_auto.remove(ctx.author.id)
            await self.update_taco({query["_id"]: taco}, {query["_id"]: taco_data})
            return await ctx.send("No interaction in 1 minute. Saving data..")

    @auto_taco.error
    async def auto_taco_error(self, ctx, error):
        custom_embed = discord.Embed(title="Failed to perfom auto taco",
                                     description=error.original
                                     if isinstance(error, commands.CommandInvokeError)
                                     else error,
                                     color=discord.Colour.red())
        await ctx.send(embed=custom_embed)
        output = ''.join(format_exception(type(error), error, error.__traceback__))
        if len(output) > 1500:
            buffer = BytesIO(output.encode("utf-8"))
            file = discord.File(buffer, filename="log.txt")
            await self.bot.send_owner(file=file)
        else:
            custom_embed = discord.Embed(title="Auto taco fail", description=f"```py\n{output}```",
                                         color=discord.Colour.red())
            await self.bot.send_owner(embed=custom_embed)


class OwO(commands.Cog):
    def __init__(self, bot: SewentyBot):
        self.bot: SewentyBot = bot

    @commands.command(aliases=["owostats", "statowo", " statsowo", "ostat"])
    async def owostat(self, ctx, users: discord.User = None):  # type: ignore
        """
        Show owo stat (with *very new* haki db)
        """
        if not users:
            users = ctx.author
        col = self.bot.LXV_DB["owo-stats"]
        query = {"$match": {"$and": [{"_id.user": ctx.author.id}, {"_id.dayId": {"$gte": 0}}]}}
        date_before = datetime(2000, 1, 1).replace(hour=0,
                                                   minute=0,
                                                   second=0,
                                                   microsecond=0,
                                                   tzinfo=pytz.timezone("US/Pacific"))
        date_now = datetime.now(dt.timezone.utc).astimezone(pytz.timezone("US/Pacific"))
        date_id = (date_now-date_before).days
        result = col.aggregate([query])
        total = 0
        first = -1
        last = 0
        last_year, this_year, last_month, this_month, last_week, this_week = 0, 0, 0, 0, 0, 0
        yesterday = 0
        today = 0
        async for row in result:
            day_id = row["_id"]["dayId"]
            owo_count = 0
            if "owoCount" in row:
                owo_count = row["owoCount"]
            if first < 0:
                first = owo_count
            if day_id == date_id-1:
                yesterday = owo_count
            if day_id == date_id:
                today = owo_count
            if date_id - (365 * 2) <= day_id <= date_id - 365:
                last_year += owo_count
            if day_id > date_id - 365:
                this_year += owo_count
            if date_id - (30 * 2) <= day_id <= date_id - 30:
                last_month += owo_count
            if day_id > date_id - 30:
                this_month += owo_count
            if date_id - (7 * 2) <= day_id <= date_id - 7:
                last_week += owo_count
            if day_id > date_id - 7:
                this_week += owo_count
            last = owo_count
            total += owo_count

        custom_embed = discord.Embed(color=discord.Colour.random())
        custom_embed.add_field(name="What is stat",
                               value=f"Total: {total}\n"
                                     f"Today: {today}\n"
                                     f"Yesterday: {yesterday}\n"
                                     f"First day: {first}\n"
                                     f"Last day: {last}",
                               inline=False)
        custom_embed.add_field(name="Not so accurate stat",
                               value=f"This week: {this_week}\n"
                                     f"This month: {this_month}\n"
                                     f"This year: {this_year}\n"
                                     f"Last week: {last_week}\n"
                                     f"Last month: {last_month}\n"
                                     f"Last year: {last_year}\n")
        custom_embed.set_author(name=users.name, icon_url=users.avatar)
        await ctx.send(embed=custom_embed)

    @commands.command(name='cp', help='Wanna search for cp?')
    async def cp_dex(self, ctx, name):
        query = {"$or": [{"aliases": name}, {"_id": name}]}
        cp_collection = self.bot.CP_DB["cp"]
        cp = await cp_collection.find_one(query)
        if cp is None:
            await ctx.reply('No cp found :c', mention_author=False)
            return
        name = cp['_id']
        hp = cp['hp']
        str_stat = cp['str']
        pr_stat = cp['pr']
        wp_stat = cp['wp']
        mag_stat = cp['mag']
        mr_stat = cp['mr']
        aliases = cp['aliases']
        month = cp['creationInfo']['month']
        year = cp['creationInfo']['year']
        image_url = cp['imageLink']
        rand_num = random.randint(0, 16777215)
        emoji_hp, emoji_att, emoji_pr, emoji_wp, emoji_mag, emoji_mr = \
            "<:hp:759752326973227029>", \
            "<:att:759752341678194708>", \
            "<:pr:759752354467414056>", \
            "<:wp:759752292713889833>", \
            "<:mag:759752304080715786>", \
            "<:mr:759752315904196618>"
        custom_embed = discord.Embed(title=name, color=rand_num)
        month = calendar.month_name[int(month)]
        if aliases:
            aliases = ', '.join(aliases)
        else:
            aliases = "None"
        custom_embed.add_field(name="Aliases", value=aliases, inline=False)
        custom_embed.add_field(name="Stats", value=f"{emoji_hp} `{hp}`  "
                                                   f"{emoji_att} `{str_stat}`  "
                                                   f"{emoji_pr} `{pr_stat}`\n"
                                                   f"{emoji_wp} `{wp_stat}`  "
                                                   f"{emoji_mag} `{mag_stat}`  "
                                                   f"'{emoji_mr} `{mr_stat}`')")
        custom_embed.set_thumbnail(url=image_url)
        custom_embed.set_footer(text=f"Created {month} {year}")
        await ctx.send(embed=custom_embed)


async def setup(bot: SewentyBot):
    await bot.add_cog(OwO(bot))
    await bot.add_cog(Taco(bot))
