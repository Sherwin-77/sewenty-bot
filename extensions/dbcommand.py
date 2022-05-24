from __future__ import annotations

import discord
from discord.ext import commands
import pytz

import asyncio
import calendar
from datetime import datetime
import datetime as dt
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import SewentyBot


# If this is working, don't touch it


class Taco(commands.Cog):
    def __init__(self, bot: SewentyBot):
        self.bot: SewentyBot = bot
        self.COLLECTION = self.bot.DB["userdata"]

        # This may be changed as soon as new location is confirmed
        self.REGISTERED_LOCATION = {"beach", "city"}
        self.REGISTERED_ETC = {"Taco Truck Upgrades 🚚": "",
                               "Ice Cream Stand Upgrades 🍦": "beach",
                               "Hotdog Cart Upgrades 🌭": "city"}
        self.SHORTCUT_LOCATION = {'s': "", 'b': "beach", "c": "city"}
        self.taco_set, self.taco_recommend = set(), set()

    @commands.command(name="tacoset", aliases=["ts"])
    async def set_taco(self, ctx, multiple: bool = False):
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
        for i in history:
            if i.author.id != 490707751832649738:
                continue
            try:
                embedded = i.embeds
                new = embedded[-1].to_dict()["description"].split('\n')
                raw_title = embedded[-1].to_dict()["title"]
                title = raw_title.split("| ")[-1]
                is_shack = False
                if "Shack" in title:
                    is_shack = True
                title = self.REGISTERED_ETC[title] if title in self.REGISTERED_ETC else title.split(" ")[0].lower()
            except KeyError:
                continue
            location = title if title in self.REGISTERED_LOCATION else ""
            if is_shack and not location:
                await ctx.send("New location detected and unregistered. Please DM invalid-user#8807")
                return
            to_update = {}
            for j in range(len(new) - 1):
                # cursor selecting the name
                if '(' not in new[j]:
                    continue
                if '✅' in new[j]:
                    to_update.update({new[j + 2].split('`')[1].capitalize(): 0})
                    continue
                if "+$" not in new[j + 2]:
                    continue
                boost = int(new[j + 2].split("/hr")[0].split('$')[-1])
                cost = int(new[j + 1].split('$')[-1].replace(',', ''))
                id_ = new[j + 3].split('`')[-2].capitalize()
                to_update.update({id_: boost / cost})
            data_id = f"{ctx.author.id}taco{location}"
            if data_id not in placeholder:
                placeholder.update({data_id: to_update})
                if multiple:
                    continue
                break
            val = placeholder[data_id]
            placeholder.update({data_id: {**val, **to_update}})
            if not multiple:
                break

        for k in placeholder:
            query = {"_id": k}
            counts = await self.COLLECTION.count_documents(query)
            if counts == 0:
                await self.COLLECTION.insert_one({"_id": k, "taco": placeholder[k]})
            else:
                old_update = await self.COLLECTION.find_one(query)
                old_update = old_update["taco"]
                merged = {**old_update, **placeholder[k]}
                await self.COLLECTION.update_one(query, {"$set": {'taco': merged}})
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

    @commands.command(name='tsrecommend', aliases=['tr'])
    async def find_taco(self, ctx, limit: int = 3, location: str = ""):
        """
        Recommend upgrade. For specific location e.g. beach:
        s!tsrecommend 3 beach
        """
        location = location.lower()
        location = location if location not in self.SHORTCUT_LOCATION else self.SHORTCUT_LOCATION[location]
        if location not in self.REGISTERED_LOCATION and location:
            await ctx.send("You input scary location to me <:blobsob:809721186966831105>", delete_after=5)
        if limit > 10:
            await ctx.send("Why booli me <:blobsob:809721186966831105> (max 10)", delete_after=5)
            return
        if str(ctx.author.id) in self.taco_recommend:
            await ctx.send("Chill down <:blobsob:809721186966831105>", delete_after=4)
            return
        query = {"_id": f'{ctx.author.id}taco{location}'}
        counts = await self.COLLECTION.count_documents(query)
        if counts == 0:
            await ctx.reply("Give taco stat when <:PaulOwO:721154434297757727>", mention_author=False, delete_after=5)
        else:
            taco = await self.COLLECTION.find_one(query)
            taco = taco["taco"]
            custom_embed = discord.Embed(title="Taco upgrade recommendation",
                                         description=f"Recommendation shows up to {limit}",
                                         color=discord.Colour.random())
            for n in range(1, limit + 1):
                t = max(taco, key=taco.get)
                v = format(taco[t], '.3e')
                taco.pop(t)
                custom_embed.add_field(name=f"Recommendation {n}", value=f"{t}\n(Value = {v})")
            custom_embed.set_author(name=f"{ctx.author.name}\'s Taco", icon_url=ctx.author.avatar)
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
            taco = await self.COLLECTION.find_one(query)
            taco = taco["taco"]
            for x in dl:
                taco.pop(x)
            await self.COLLECTION.update_one(query, {"$set": {'taco': taco}})
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
            taco = await self.COLLECTION.find_one(query)
            taco = taco["taco"]
            for x in dl:
                taco.pop(x)
            await self.COLLECTION.update_one({"_id": f"{ctx.author.id}tacobeach"}, {"$set": {"taco": taco}})
            await ctx.message.add_reaction('👍')
        self.taco_set.add(str(ctx.author.id))
        await asyncio.sleep(2)
        self.taco_set.remove(str(ctx.author.id))

    @commands.command(name="tsclearcart", aliases=['tcc'])
    async def delete_stand(self, ctx):
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
            taco = await self.COLLECTION.find_one(query)
            taco = taco["taco"]
            for x in dl:
                taco.pop(x)
            await self.COLLECTION.update_one(query, {"$set": {"taco": taco}})
            await ctx.message.add_reaction('👍')
        self.taco_set.add(str(ctx.author.id))
        await asyncio.sleep(2)
        self.taco_set.remove(str(ctx.author.id))


class OwO(commands.Cog):
    def __init__(self, bot: SewentyBot):
        self.bot: SewentyBot = bot

    @commands.command(name='owostat', help='show your owo stat (by hakibot)',
                      aliases=['owostats', 'statowo', ' statsowo'])
    async def statowo(self, ctx, users: discord.User = None):
        if not users:
            users = ctx.author
        yellow = 0xfff00
        col = self.bot.CP_DB["owo-count"]
        query = {'user': users.id, 'guild': ctx.guild.id}
        if col.count_documents(query) == 0:
            await ctx.send('User doesnt have any owostat in this guild')
        result = await col.find_one(query)
        owo_count = result['owoCount']
        daily_count = result['dailyCount']
        yesterday_count = result['yesterdayCount']
        weekly_count = result['weeklyCount']
        last_week_count = result['lastWeekCount']
        monthly_count = result['monthlyCount']
        last_month_count = result['lastMonthCount']
        yearly_count = result['yearlyCount']
        last_year_count = result['lastYearCount']
        custom_embed = discord.Embed(title=f'{users.name}\'s owostat',
                                     description=f'Total: {owo_count}', color=yellow)
        custom_embed.add_field(name='Current stat',
                               value=f'Today: {daily_count}\n'
                               f'This week: {weekly_count}\n'
                               f'This month: {monthly_count}\n'
                               f'This year: {yearly_count}', inline=False)
        custom_embed.add_field(name='Past stat',
                               value=f'Yesterday: {yesterday_count}\n'
                               f'Last week: {last_week_count}\n'
                               f'Last month: {last_month_count}\n'
                               f'Last year: {last_year_count}')
        custom_embed.set_author(name=users.name, icon_url=users.avatar)
        await ctx.send(embed=custom_embed)

    @commands.command(aliases=["ldb", "top", "owotop"])
    async def leaderboard(self, ctx, *option):
        """
        OwO leaderboard using haki db
        """
        find_by = None
        limit = 5
        date_now = discord.utils.snowflake_time(ctx.message.id).replace(tzinfo=pytz.utc).astimezone(
            pytz.timezone('US/Pacific')).replace(hour=0, minute=0, second=0, microsecond=0)
        matching = {'lastyear': 'lastYearCount',
                    'ly': 'lastYearCount',
                    'lastmonth': 'lastMonthCount',
                    'lm': 'lastMonthCount',
                    'lastweek': 'lastWeekCount',
                    'lw': 'lastWeekCount',
                    'y': 'yesterdayCount',
                    'yesterday': 'yesterdayCount',
                    'year': 'yearlyCount',
                    'month': 'monthlyCount',
                    'm': 'monthlyCount',
                    'week': 'weeklyCount',
                    'w': 'weeklyCount',
                    'today': 'dailyCount',
                    't': 'dailyCount'}
        if option:
            for x in option:
                if x.lower() in matching and not find_by:
                    find_by = matching[x.lower()]
                elif x.isdigit():
                    if int(x) > 25:
                        await ctx.send('Give valid number when', delete_after=5)
                        return
                    else:
                        limit = int(x)
                else:
                    await ctx.send('What are you trying to do?', delete_after=5)
                    return
            if not find_by:
                find_by = 'owoCount'
        else:
            find_by = 'owoCount'
            limit = 5

        if find_by == 'dailyCount':
            epoch = datetime.timestamp(date_now) * 1000
        elif find_by == 'weeklyCount':
            epoch = datetime.timestamp(date_now - dt.timedelta(days=(date_now.weekday() + 1) % 7)) * 1000
        elif find_by == 'monthlyCount':
            epoch = datetime.timestamp(date_now.replace(day=1)) * 1000
        elif find_by == 'yearlyCount':
            epoch = datetime.timestamp(date_now.replace(month=1, day=1)) * 1000
        elif find_by == 'yesterdayCount':
            epoch = datetime.timestamp(date_now - dt.timedelta(days=1)) * 1000
        elif find_by == 'lastWeekCount':
            epoch = datetime.timestamp(date_now - dt.timedelta(days=((date_now.weekday() + 1) % 7) + 7)) * 1000
        elif find_by == 'lastMonthCount':
            epoch = datetime.timestamp((date_now.replace(day=1) - dt.timedelta(days=1)).replace(day=1)) * 1000
        elif find_by == 'lastYearCount':
            epoch = datetime.timestamp((date_now.replace(month=1, day=1) - dt.timedelta(days=1)).replace(day=1)) * 1000
        else:
            epoch = 0

        leaderboard = self.bot.CP_DB['owo-count'].aggregate(
            [{'$match': {'$and': [{'guild': ctx.guild.id}, {'lastOWO': {'$gte': epoch}}]}},
             {'$project': {'_id': 0, 'user': 1, find_by: 1}},
             {'$sort': {find_by: -1}}, {'$limit': limit}])
        leaderboard_embed = discord.Embed(title='Leaderboard', color=discord.Colour.random())
        order = 0
        async for line in leaderboard:
            order += 1
            user = await self.bot.fetch_user(line['user'])
            leaderboard_embed.add_field(name=f'[{order}]: {user.name}', value=f'{line[find_by]} OwOs', inline=False)
        await ctx.send(embed=leaderboard_embed)

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
