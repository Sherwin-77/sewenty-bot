import discord
from discord.ext import commands
import asyncio
import random
import os
import pytz
from pymongo import MongoClient
from datetime import datetime
import datetime as dt
import calendar

EMAILS = os.getenv('EMAIL')
PASSWORDS = os.getenv('PASSWORD')
SECOND_EMAIL = os.getenv("NEXT_EMAIL")
SECOND_PASSWORD = os.getenv("NEXT_PASSWORD")

MANGO_URL = f'mongodb+srv://{EMAILS}:{PASSWORDS}@clusterdiscord.8dm0p.mongodb.net/test'
CLUSTER = MongoClient(MANGO_URL)
DB = CLUSTER["Data"]
COLLECTION = DB["userdata"]

CP_URL = f'mongodb+srv://{SECOND_EMAIL}:{SECOND_PASSWORD}@hakiobo.s5buy.mongodb.net/Hakibot'
CP_CLUSTER = MongoClient(CP_URL)
CP_DB = CP_CLUSTER["Hakibot"]
CP_COLLECTION = CP_DB["cp"]


# This may be changed as soon as new location is confirmed
REGISTERED_LOCATION = {"beach", "city"}
REGISTERED_ETC = {"Ice Cream Stand Upgrades 🍦": "beach", "Taco Truck Upgrades 🚚": "",
                  "Hotdog Cart Upgrades 🌭": "city"}
SHORTCUT_LOCATION = {'s': "", 'b': "beach", "c": "city"}
taco_set, taco_recommend = set(), set()


class Taco(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="tacoset", help="Set your taco value based on embed\n"
                                           "Detect up to 5 message if not multiple else 8\n"
                                           "To set multiple set: s!tacoset true", aliases=["ts"])
    async def set_taco(self, ctx, multiple: bool = False):
        if str(ctx.author.id) in taco_set:
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
                title = REGISTERED_ETC[title] if title in REGISTERED_ETC else title.split(" ")[0].lower()
            except KeyError:
                continue
            location = title if title in REGISTERED_LOCATION else ""
            print(location)
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
                if '+$' not in new[j + 2]:
                    continue
                boost = int(new[j + 2].split("/hr")[0].split("$")[-1])
                cost = int(new[j + 1].split("$")[-1].replace(',', ''))
                id_ = new[j + 3].split("`")[-2].capitalize()
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
                print(True)
                break

        for k in placeholder:
            if COLLECTION.count_documents({"_id": k}) == 0:
                COLLECTION.insert_one({"_id": k, 'taco': placeholder[k]})
            else:
                old_update = COLLECTION.find_one({"_id": k})['taco']
                merged = {**old_update, **placeholder[k]}
                COLLECTION.update_one({"_id": k}, {"$set": {'taco': merged}})
        await ctx.message.add_reaction('👍')

        if multiple:
            def check(reaction, users):
                return users == ctx.author and str(reaction.emoji) == "❗" and reaction.message == ctx.message

            await ctx.message.add_reaction("❗")
            try:
                emoji, user = await self.bot.wait_for("reaction_add", timeout=30, check=check)
            except asyncio.TimeoutError:
                return
            await ctx.send("Multiple check feature look up to **8 messages** before you and it **overrides** "
                           "older embed if newer one is the same so be careful")
        taco_set.add(str(ctx.author.id))
        await asyncio.sleep(2)
        taco_set.remove(str(ctx.author.id))

    @commands.command(name='tsrecommend', help="Recommend upgrade. For specific location e.g beach:\n"
                                               "s!tsrecommend 3 beach", aliases=['tr'])
    async def find_taco(self, ctx, limit: int = 3, location: str = ""):
        location = location.lower()
        location = location if location not in SHORTCUT_LOCATION else SHORTCUT_LOCATION[location]
        if location not in REGISTERED_LOCATION and location:
            await ctx.send("You input scary location to me <:blobsob:809721186966831105>", delete_after=5)
        if limit > 10:
            await ctx.send("Why booli me <:blobsob:809721186966831105> (max 10)", delete_after=5)
            return
        if str(ctx.author.id) in taco_recommend:
            await ctx.send("Chill down <:blobsob:809721186966831105>", delete_after=4)
            return
        form = {"_id": f'{ctx.author.id}taco{location}'}
        if COLLECTION.count_documents(form) == 0:
            await ctx.reply("Give taco stat when <:PaulOwO:721154434297757727>", mention_author=False, delete_after=5)
        else:
            rand_num = random.randint(0, 16777215)
            taco = COLLECTION.find(form)[0]['taco']
            tcemb = discord.Embed(title='Taco upgrade recommendation',
                                  description=f'Recommendation shows up to {limit}',
                                  color=rand_num)
            for x in range(1, limit + 1):
                t = max(taco, key=taco.get)
                v = format(taco[t], '.3e')
                taco.pop(t)
                tcemb.add_field(name=f'Recommendation {x}', value=f'{t}\n(Value = {v})')
            tcemb.set_author(name=f'{ctx.author.name}\'s Taco', icon_url=ctx.author.avatar_url)
            await ctx.send(embed=tcemb)
        taco_recommend.add(str(ctx.author.id))
        await asyncio.sleep(4)
        taco_recommend.remove(str(ctx.author.id))

    @commands.command(name='tscleartruck', aliases=['tct'])
    async def delete_truck(self, ctx):
        if str(ctx.author.id) in taco_set:
            await ctx.send('Chill down <:blobsob:809721186966831105>', delete_after=2)
            return
        dl = ['Register', 'Assistant', 'Driver', 'Kitchen', 'Engine']
        form = {"_id": f'{ctx.author.id}taco'}
        if COLLECTION.count_documents(form) == 0:
            await ctx.reply('Your data not exist <:PaulOwO:721154434297757727>', mention_author=False, delete_after=5)
        else:
            taco = COLLECTION.find_one(form)['taco']
            for x in dl:
                taco.pop(x)
            COLLECTION.update_one({"_id": f'{ctx.author.id}taco'}, {"$set": {'taco': taco}})
            await ctx.message.add_reaction('👍')
        taco_set.add(str(ctx.author.id))
        await asyncio.sleep(2)
        taco_set.remove(str(ctx.author.id))

    @commands.command(name='tsclearstand', aliases=['tcs'])
    async def delete_stand(self, ctx):
        if str(ctx.author.id) in taco_set:
            await ctx.send('Chill down <:blobsob:809721186966831105>', delete_after=2)
            return
        dl = ['Decals', 'Wheels', 'Mixers', 'Server', 'Freezer']
        form = {"_id": f'{ctx.author.id}tacobeach'}
        if COLLECTION.count_documents(form) == 0:
            await ctx.reply('Your data not exist <:PaulOwO:721154434297757727>', mention_author=False,
                            delete_after=5)
        else:
            taco = COLLECTION.find_one(form)['taco']
            for x in dl:
                taco.pop(x)
            COLLECTION.update_one({"_id": f'{ctx.author.id}tacobeach'}, {"$set": {'taco': taco}})
            await ctx.message.add_reaction('👍')
        taco_set.add(str(ctx.author.id))
        await asyncio.sleep(2)
        taco_set.remove(str(ctx.author.id))

    @commands.command(name='tsclearcart', aliases=['tcc'])
    async def delete_stand(self, ctx):
        if str(ctx.author.id) in taco_set:
            await ctx.send('Chill down <:blobsob:809721186966831105>', delete_after=2)
            return
        dl = ["Buns", "Condiments", "Beverages", "Coolers", "Grill"]
        form = {"_id": f'{ctx.author.id}tacocity'}
        if COLLECTION.count_documents(form) == 0:
            await ctx.reply('Your data not exist <:PaulOwO:721154434297757727>', mention_author=False,
                            delete_after=5)
        else:
            taco = COLLECTION.find_one(form)['taco']
            for x in dl:
                taco.pop(x)
            COLLECTION.update_one({"_id": f'{ctx.author.id}tacocity'}, {"$set": {'taco': taco}})
            await ctx.message.add_reaction('👍')
        taco_set.add(str(ctx.author.id))
        await asyncio.sleep(2)
        taco_set.remove(str(ctx.author.id))


class OwO(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='owobremind', help='Toggle owob reminder', aliases=['battle', 'b'])
    async def toggleowob(self, ctx):
        userid = ctx.author.id
        yellow = 0xfff00
        red = 0xff0000
        form = {"_id": userid}
        now = False
        newparam = -1
        if COLLECTION.count_documents(form) == 0:
            post = {"_id": userid, "param": 3}
            COLLECTION.insert_one(post)
            now = True
        else:
            user = COLLECTION.find(form)

            for result in user:
                user = result["param"]
            if user == -1:
                newparam = 3
                now = True
            elif user == 1:
                newparam = 2
                now = True
            elif user == 2:
                newparam = 1
                now = False
            elif user == 3:
                newparam = -1
                now = False
            COLLECTION.update_one({"_id": userid}, {"$set": {"param": newparam}})
        if now:
            custom_embed = discord.Embed(title="Changed your setting",
                                         description=f'Setting changed into: **{str(now)}** :white_check_mark: ',
                                         color=yellow)
        else:
            custom_embed = discord.Embed(title="Changed your setting",
                                         description=f'Setting changed into: **{str(now)}** '
                                                     f':negative_squared_cross_mark:  ',
                                         color=red)
        await ctx.send(embed=custom_embed)

    @commands.command(name='owohremind', help='Toggle owoh reminder', aliases=['hunt', 'h'])
    async def toggleowoh(self, ctx):
        userid = ctx.author.id
        yellow = 0xfff00
        red = 0xff0000
        form = {"_id": userid}
        now = False
        newparam = -1
        if COLLECTION.count_documents(form) == 0:
            post = {"_id": userid, "param": 3}
            COLLECTION.insert_one(post)
            now = True
        else:
            user = COLLECTION.find(form)

            for result in user:
                user = result["param"]
            if user == -1:
                newparam = 1
                now = True
            if user == 1:
                newparam = -1
                now = False
            if user == 2:
                newparam = 3
                now = False
            if user == 3:
                newparam = 2
                now = True
            COLLECTION.update_one({"_id": userid}, {"$set": {"param": newparam}})
        if now:
            custom_embed = discord.Embed(title="Changed your setting",
                                         description=f'Setting changed into: **{str(now)}** :white_check_mark: ',
                                         color=yellow)
        else:
            custom_embed = discord.Embed(title="Changed your setting",
                                         description=f'Setting changed into: **{str(now)}** :negative_squared_cross_mark:  ',
                                         color=red)
        await ctx.send(embed=custom_embed)

    @commands.command(name='owoprefix', help='Set owoprefix')
    @commands.has_permissions(administrator=True)
    async def owoprefix(self, ctx, prefix: str = None):
        guildid = ctx.guild.id
        form = {"_id": guildid}
        if prefix:
            if COLLECTION.count_documents(form) == 0:
                post = {"_id": guildid, "owoprefix": prefix}
                COLLECTION.insert_one(post)
                await ctx.send("changed into: " + str(prefix))
            else:
                COLLECTION.update_one({"_id": guildid}, {"$set": {"owoprefix": prefix}})
                await ctx.send("changed into: " + str(prefix))
        else:
            if COLLECTION.count_documents(form) == 0:
                await ctx.send("No custom owoprefix here")
            else:
                user = COLLECTION.find_one(form)
                oprefix = user["owoprefix"]
                await ctx.send("Current owoprefix is: " + str(oprefix))

    @commands.command(name='||owoprefix||', help='Force change owoprefix', hidden=True)
    async def owoprefix1(self, ctx, prefix: str = None):
        guildid = ctx.guild.id
        userid = ctx.author.id
        form = {"_id": guildid}
        if userid == 436376194166816770:
            if prefix:
                if COLLECTION.count_documents(form) == 0:
                    post = {"_id": guildid, "owoprefix": prefix}
                    COLLECTION.insert_one(post)
                    await ctx.send("changed into: " + str(prefix))
                else:
                    COLLECTION.update_one({"_id": guildid}, {"$set": {"owoprefix": prefix}})
                    await ctx.send("changed into: " + str(prefix))
            else:
                if COLLECTION.count_documents(form) == 0:
                    await ctx.send("No custom owoprefix here")
                else:
                    user = COLLECTION.find_one(form)
                    oprefix = user["owoprefix"]
                    await ctx.send("Current owoprefix is: " + str(oprefix))
        else:
            await ctx.send("Only bot owner can do this")

    @commands.command(name='owostat', help='show your owo stat (by hakibot)',
                      aliases=['owostats', 'statowo', ' statsowo'])
    async def statowo(self, ctx, users: discord.User = None):
        if not users:
            users = ctx.author
        yellow = 0xfff00
        col = CP_DB['owo-count']
        form = {'user': users.id, 'guild': ctx.guild.id}
        if col.count_documents(form) == 0:
            await ctx.send('User doesnt have any owostat in this guild')
        result = col.find_one(form)
        owocount = result['owoCount']
        dailycount = result['dailyCount']
        yesterdaycount = result['yesterdayCount']
        weeklycount = result['weeklyCount']
        lastweekcount = result['lastWeekCount']
        monthlycount = result['monthlyCount']
        lastmonthcount = result['lastMonthCount']
        yearlycount = result['yearlyCount']
        lastyearcount = result['lastYearCount']
        cembed = discord.Embed(title=f'{users.name}\'s owostat',
                               description=f'Total: {owocount}', color=yellow)
        cembed.add_field(name='Current stat',
                         value=f'Today: {dailycount}\n'
                               f'This week: {weeklycount}\n'
                               f'This month: {monthlycount}\n'
                               f'This year: {yearlycount}', inline=False)
        cembed.add_field(name='Past stat',
                         value=f'Yesterday: {yesterdaycount}\n'
                               f'Last week: {lastweekcount}\n'
                               f'Last month: {lastmonthcount}\n'
                               f'Last year: {lastyearcount}')
        cembed.set_author(name=users.name, icon_url=users.avatar_url)
        await ctx.send(embed=cembed)

    @commands.command(name='leaderboard', aliases=['ldb', 'top', 'owotop'], help='leaderboard (by hakibot)')
    async def listo(self, ctx, *option):
        find_by = None
        limit = 5
        rand_num = random.randint(0, 16777215)
        datenow = discord.utils.snowflake_time(ctx.message.id).replace(tzinfo=pytz.utc).astimezone(
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
            epoch = datetime.timestamp(datenow) * 1000
        elif find_by == 'weeklyCount':
            epoch = datetime.timestamp(datenow - dt.timedelta(days=(datenow.weekday() + 1) % 7)) * 1000
        elif find_by == 'monthlyCount':
            epoch = datetime.timestamp(datenow.replace(day=1)) * 1000
        elif find_by == 'yearlyCount':
            epoch = datetime.timestamp(datenow.replace(month=1, day=1)) * 1000
        elif find_by == 'yesterdayCount':
            epoch = datetime.timestamp(datenow - dt.timedelta(days=1)) * 1000
        elif find_by == 'lastWeekCount':
            epoch = datetime.timestamp(datenow - dt.timedelta(days=((datenow.weekday() + 1) % 7) + 7)) * 1000
        elif find_by == 'lastMonthCount':
            epoch = datetime.timestamp((datenow.replace(day=1) - dt.timedelta(days=1)).replace(day=1)) * 1000
        elif find_by == 'lastYearCount':
            epoch = datetime.timestamp((datenow.replace(month=1, day=1) - dt.timedelta(days=1)).replace(day=1)) * 1000
        else:
            epoch = 0

        leaderboard = CP_DB['owo-count'].aggregate(
            [{'$match': {'$and': [{'guild': ctx.guild.id}, {'lastOWO': {'$gte': epoch}}]}},
             {'$project': {'_id': 0, 'user': 1, find_by: 1}},
             {'$sort': {find_by: -1}}, {'$limit': limit}])
        leaderboard_embed = discord.Embed(title='Leaderboard', color=rand_num)
        order = 0
        for y in leaderboard:
            order += 1
            user = await self.bot.fetch_user(y['user'])
            leaderboard_embed.add_field(name=f'[{order}]: {user.name}', value=f'{y[find_by]} OwOs', inline=False)
        await ctx.send(embed=leaderboard_embed)

    @commands.command(name='cp', help='Wanna search for cp?')
    async def cpdex(self, ctx, name):
        form = {"$or": [{"aliases": name}, {"_id": name}]}
        cp = CP_COLLECTION.find_one(form)
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
        ehp, eatt, epr, ewp, emag, emr = '<:hp:759752326973227029>', '<:att:759752341678194708>', \
                                         '<:pr:759752354467414056>', '<:wp:759752292713889833>', \
                                         '<:mag:759752304080715786>', '<:mr:759752315904196618>'
        custom_embed = discord.Embed(title=name, color=rand_num)
        month = calendar.month_name[int(month)]
        if aliases:
            aliases = ', '.join(aliases)
        else:
            aliases = 'None'
        custom_embed.add_field(name='Aliases', value=aliases, inline=False)
        custom_embed.add_field(name='Stats', value=f'{ehp} `{hp}`  {eatt} `{str_stat}`  {epr} `{pr_stat}`\n'
                                                   f'{ewp} `{wp_stat}`  {emag} `{mag_stat}`  {emr} `{mr_stat}`')
        custom_embed.set_thumbnail(url=image_url)
        custom_embed.set_footer(text=f'Created {month} {year}')
        await ctx.send(embed=custom_embed)


def setup(bot):
    bot.add_cog(OwO(bot))
    bot.add_cog(Taco(bot))