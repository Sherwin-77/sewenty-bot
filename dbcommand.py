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

emails = os.getenv('EMAIL')
passwords = os.getenv('PASSWORD')
second_email = os.getenv("NEXT_EMAIL")
second_password = os.getenv("NEXT_PASSWORD")

tacoset, tacorecommend = {}, {}

mangourl = f'mongodb+srv://{emails}:{passwords}@clusterdiscord.8dm0p.mongodb.net/test'
cluster = MongoClient(mangourl)
db = cluster["Data"]
collection = db["userdata"]

cpurl = f'mongodb+srv://{second_email}:{second_password}@hakiobo.s5buy.mongodb.net/Hakibot'
cpcluster = MongoClient(cpurl)
cpdb = cpcluster["Hakibot"]
cpcollection = cpdb["cp"]


class Taco(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='tacoset', aliases=['ts'])
    async def calculator(self, ctx, trait: str = None, price: int = None):
        if str(ctx.author.id) in tacoset:
            await ctx.send('Chill down <:blobsob:809721186966831105>', delete_after=2)
            return
        totallist = {'Newspaper': 10, 'Radio': 20, 'Email': 30, 'Internet': 50, 'Tv': 160, 'Blimp': 200, 'Flowers': 5,
                     'Ornaments': 10, 'Lights': 30, 'Mural': 100,
                     'Statue': 400, 'Paint': 10, 'Furniture': 20, 'Bathrooms': 25, 'Billboard': 35, 'Apprentice': 10,
                     'Cook': 20, 'Sous': 40, 'Head': 65,
                     'Executive': 150, 'Advertiser': 20, 'Greeter': 25, 'Register': 50, 'Assistant': 100, 'Driver': 250,
                     'Kitchen': 400, 'Engine': 1000, 'Tipjar': -1,
                     'Appliances': -1}
        if trait is None and price is None:
            y = {}
            to_update = {}
            found = False
            async for x in ctx.message.channel.history(limit=5):
                if x.author.id == 490707751832649738:
                    embedded = x.embeds
                    for y in embedded:
                        y = y.to_dict()
                    new = y['description'].split('\n')
                    for z in range(len(new) - 1):
                        if '✅' in new[z]:
                            to_update.update({new[z + 2].split('`')[1].capitalize(): 0})
                        if 'Cost' in new[z]:
                            to_update.update({new[z + 2].split('`')[1].capitalize(): totallist[new[z + 2].split('`')[
                                1].capitalize()] / int(new[z].split(':')[1].replace('$', '').replace(',', ''))})
                    if not to_update:
                        return
                    form = {"_id": f'{ctx.author.id}taco'}
                    if collection.count_documents(form) == 0:
                        collection.insert_one({"_id": f'{ctx.author.id}taco', 'taco': to_update})
                    else:
                        old_update = collection.find(form)[0]['taco']
                        merged = {**old_update, **to_update}
                        collection.update_one({"_id": f'{ctx.author.id}taco'}, {"$set": {'taco': merged}})
                    await ctx.message.add_reaction('👍')
                    found = True
                    break
            if not found:
                await ctx.reply('Taco embed where <:PaulOwO:721154434297757727>', mention_author=False, delete_after=5)
        elif trait and price:
            form = {"_id": f'{ctx.author.id}taco'}
            trait = trait.capitalize()
            if trait in totallist:
                old_update = collection.find(form)[0]['taco']
                old_update.update({trait: price})
                collection.update_one({"_id": f'{ctx.author.id}taco'}, {"$set": {'taco': old_update}})
                await ctx.message.add_reaction('👍')
            else:
                await ctx.reply('Valid id when <:PaulOwO:721154434297757727>', mention_author=False, delete_after=5)
        tacoset.update({str(ctx.author.id): True})
        await asyncio.sleep(2)
        tacoset.pop(str(ctx.author.id))

    @commands.command(name='tsrecommend', aliases=['tr'])
    async def findtaco(self, ctx, limit: int = 3):
        if limit > 10:
            await ctx.send('Why booli me <:blobsob:809721186966831105> (max 10)', delete_after=5)
            return
        if str(ctx.author.id) in tacorecommend:
            await ctx.send('Chill down <:blobsob:809721186966831105>', delete_after=4)
            return
        form = {"_id": f'{ctx.author.id}taco'}
        if collection.count_documents(form) == 0:
            await ctx.reply('Give taco stat when <:PaulOwO:721154434297757727>', mention_author=False, delete_after=5)
        else:
            randnum = random.randint(0, 16777215)
            taco = collection.find(form)[0]['taco']
            tcemb = discord.Embed(title='Taco upgrade recommendation',
                                  description=f'Recommendation shows up to {limit}',
                                  color=randnum)
            for x in range(1, limit + 1):
                t = max(taco, key=taco.get)
                v = format(taco[t], '.3e')
                taco.pop(t)
                tcemb.add_field(name=f'Recommendation {x}', value=f'{t}\n(Value = {v})')
            tcemb.set_author(name=f'{ctx.author.name}\'s Taco', icon_url=ctx.author.avatar_url)
            await ctx.send(embed=tcemb)
        tacorecommend.update({str(ctx.author.id): True})
        await asyncio.sleep(4)
        tacorecommend.pop(str(ctx.author.id))

    @commands.command(name='tscleartruck', aliases=['tct'])
    async def delete_truck(self, ctx):
        dl = ['Register', 'Assistant', 'Driver', 'Kitchen', 'Engine']
        form = {"_id": f'{ctx.author.id}taco'}
        if collection.count_documents(form) == 0:
            await ctx.reply('Your data not exist <:PaulOwO:721154434297757727>', mention_author=False, delete_after=5)
        else:
            taco = collection.find(form)[0]['taco']
            for x in dl:
                taco.pop(x)
            collection.update_one({"_id": f'{ctx.author.id}taco'}, {"$set": {'taco': taco}})
            await ctx.message.add_reaction('👍')

    @commands.command(name='tsbeachset', aliases=['tbs'])
    async def beachcalc(self, ctx, trait: str = None, price: int = None):
        if str(ctx.author.id) in tacoset:
            await ctx.send('Chill down <:blobsob:809721186966831105>', delete_after=2)
            return
        totallist = {'Newspaper': 10, 'Radio': 20, 'Email': 30, 'Internet': 50, 'Tv': 160, 'Blimp': 200,
                     'Shells': 5, 'Umbrella': 10, 'Leis': 30, 'Tanks': 125,
                     'Fountain': 500, 'Paint': 10, 'Furniture': 20, 'Bathrooms': 25, 'Billboard': 35,
                     'Apprentice': 10, 'Cook': 20, 'Sous': 40, 'Head': 65,
                     'Executive': 150, 'Advertiser': 20, 'Greeter': 25,
                     'Decals': 50, 'Wheels': 100, 'Mixers': 250, 'Server': 400, 'Freezer': 750,
                     'Tipjar': -1, 'Appliances': -1}
        if trait is None and price is None:
            y = {}
            to_update = {}
            found = False
            async for x in ctx.message.channel.history(limit=5):
                if x.author.id == 490707751832649738:
                    embedded = x.embeds
                    for y in embedded:
                        y = y.to_dict()
                    new = y['description'].split('\n')
                    for z in range(len(new) - 1):
                        if '✅' in new[z]:
                            to_update.update({new[z + 2].split('`')[1].capitalize(): 0})
                        if 'Cost' in new[z]:
                            to_update.update({new[z + 2].split('`')[1].capitalize(): totallist[new[z + 2].split('`')[
                                1].capitalize()] / int(new[z].split(':')[1].replace('$', '').replace(',', ''))})
                    if not to_update:
                        return
                    form = {"_id": f'{ctx.author.id}tacobeach'}
                    if collection.count_documents(form) == 0:
                        collection.insert_one({"_id": f'{ctx.author.id}tacobeach', 'taco': to_update})
                    else:
                        old_update = collection.find(form)[0]['taco']
                        merged = {**old_update, **to_update}
                        collection.update_one({"_id": f'{ctx.author.id}tacobeach'}, {"$set": {'taco': merged}})
                    await ctx.message.add_reaction('👍')
                    found = True
                    break
            if not found:
                await ctx.reply('Taco embed where <:PaulOwO:721154434297757727>', mention_author=False, delete_after=5)
        elif trait and price:
            form = {"_id": f'{ctx.author.id}tacobeach'}
            trait = trait.capitalize()
            if trait in totallist:
                old_update = collection.find(form)[0]['taco']
                old_update.update({trait: price})
                collection.update_one({"_id": f'{ctx.author.id}tacobeach'}, {"$set": {'taco': old_update}})
                await ctx.message.add_reaction('👍')
            else:
                await ctx.reply('Valid id when <:PaulOwO:721154434297757727>', mention_author=False, delete_after=5)
        tacoset.update({str(ctx.author.id): True})
        await asyncio.sleep(2)
        tacoset.pop(str(ctx.author.id))

    @commands.command(name='tsbeachrecommend', aliases=['tbr'])
    async def findtacobeach(self, ctx, limit: int = 3):
        if limit > 10:
            await ctx.send('Why booli me <:blobsob:809721186966831105> (max 10)', delete_after=5)
            return
        if str(ctx.author.id) in tacorecommend:
            await ctx.send('Chill down <:blobsob:809721186966831105>', delete_after=4)
            return
        form = {"_id": f'{ctx.author.id}tacobeach'}
        if collection.count_documents(form) == 0:
            await ctx.reply('Give taco stat when <:PaulOwO:721154434297757727>', mention_author=False, delete_after=5)
        else:
            randnum = random.randint(0, 16777215)
            taco = collection.find(form)[0]['taco']
            tcemb = discord.Embed(title='Taco upgrade recommendation',
                                  description=f'Recommendation shows up to {limit}',
                                  color=randnum)
            for x in range(1, limit + 1):
                t = max(taco, key=taco.get)
                v = format(taco[t], '.3e')
                taco.pop(t)
                tcemb.add_field(name=f'Recommendation {x}', value=f'{t}\n(Value = {v})')
            tcemb.set_author(name=f'{ctx.author.name}\'s Taco', icon_url=ctx.author.avatar_url)
            await ctx.send(embed=tcemb)
        tacorecommend.update({str(ctx.author.id): True})
        await asyncio.sleep(4)
        tacorecommend.pop(str(ctx.author.id))

    @commands.command(name='tsclearstand', aliases=['tcs'])
    async def delete_stand(self, ctx):
        dl = ['Decals', 'Wheels', 'Mixers', 'Server', 'Freezer']
        form = {"_id": f'{ctx.author.id}tacobeach'}
        if collection.count_documents(form) == 0:
            await ctx.reply('Your data not exist <:PaulOwO:721154434297757727>', mention_author=False, delete_after=5)
        else:
            taco = collection.find(form)[0]['taco']
            for x in dl:
                taco.pop(x)
            collection.update_one({"_id": f'{ctx.author.id}tacobeach'}, {"$set": {'taco': taco}})
            await ctx.message.add_reaction('👍')


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
        if collection.count_documents(form) == 0:
            post = {"_id": userid, "param": 3}
            collection.insert_one(post)
            now = True
        else:
            user = collection.find(form)

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
            collection.update_one({"_id": userid}, {"$set": {"param": newparam}})
        if now:
            custom_embed = discord.Embed(title="Changed your setting",
                                         description=f'Setting changed into: **{str(now)}** :white_check_mark: ',
                                         color=yellow)
        else:
            custom_embed = discord.Embed(title="Changed your setting",
                                         description=f'Setting changed into: **{str(now)}** :negative_squared_cross_mark:  ',
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
        if collection.count_documents(form) == 0:
            post = {"_id": userid, "param": 3}
            collection.insert_one(post)
            now = True
        else:
            user = collection.find(form)

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
            collection.update_one({"_id": userid}, {"$set": {"param": newparam}})
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
            if collection.count_documents(form) == 0:
                post = {"_id": guildid, "owoprefix": prefix}
                collection.insert_one(post)
                await ctx.send("changed into: " + str(prefix))
            else:
                collection.update_one({"_id": guildid}, {"$set": {"owoprefix": prefix}})
                await ctx.send("changed into: " + str(prefix))
        else:
            if collection.count_documents(form) == 0:
                await ctx.send("No custom owoprefix here")
            else:
                user = collection.find_one(form)
                oprefix = user["owoprefix"]
                await ctx.send("Current owoprefix is: " + str(oprefix))

    @commands.command(name='||owoprefix||', help='Force change owoprefix', hidden=True)
    async def owoprefix1(self, ctx, prefix: str = None):
        guildid = ctx.guild.id
        userid = ctx.author.id
        form = {"_id": guildid}
        if userid == 436376194166816770:
            if prefix:
                if collection.count_documents(form) == 0:
                    post = {"_id": guildid, "owoprefix": prefix}
                    collection.insert_one(post)
                    await ctx.send("changed into: " + str(prefix))
                else:
                    collection.update_one({"_id": guildid}, {"$set": {"owoprefix": prefix}})
                    await ctx.send("changed into: " + str(prefix))
            else:
                if collection.count_documents(form) == 0:
                    await ctx.send("No custom owoprefix here")
                else:
                    user = collection.find_one(form)
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
        col = cpdb['owo-count']
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
        randnum = random.randint(0, 16777215)
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
        elif find_by == 'montlyCount':
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

        leaderboard = cpdb['owo-count'].aggregate(
            [{'$match': {'$and': [{'guild': ctx.guild.id}, {'lastOWO': {'$gte': epoch}}]}},
             {'$project': {'_id': 0, 'user': 1, find_by: 1}},
             {'$sort': {find_by: -1}}, {'$limit': limit}])
        lembed = discord.Embed(title='Leaderboard', color=randnum)
        order = 0
        for y in leaderboard:
            order += 1
            user = await self.bot.fetch_user(y['user'])
            lembed.add_field(name=f'[{order}]: {user.name}', value=f'{y[find_by]} OwOs', inline=False)
        await ctx.send(embed=lembed)

    @commands.command(name='cp', help='Wanna search for cp?')
    async def cpdex(self, ctx, name):
        form = {"$or": [{"aliases": name}, {"_id": name}]}
        cp = cpcollection.find_one(form)
        if cp is None:
            await ctx.reply('No cp found :c', mention_author=False)
            return
        name = cp['_id']
        hp = cp['hp']
        strstat = cp['str']
        prstat = cp['pr']
        wpstat = cp['wp']
        magstat = cp['mag']
        mrstat = cp['mr']
        aliases = cp['aliases']
        month = cp['creationInfo']['month']
        year = cp['creationInfo']['year']
        imageurl = cp['imageLink']
        randnum = random.randint(0, 16777215)
        ehp, eatt, epr, ewp, emag, emr = '<:hp:759752326973227029>', '<:att:759752341678194708>', '<:pr:759752354467414056>', '<:wp:759752292713889833>', '<:mag:759752304080715786>', '<:mr:759752315904196618>'
        custom_embed = discord.Embed(title=name, color=randnum)
        month = calendar.month_name[int(month)]
        if aliases:
            aliases = ', '.join(aliases)
        else:
            aliases = 'None'
        custom_embed.add_field(name='Aliases', value=aliases, inline=False)
        custom_embed.add_field(name='Stats', value=f'{ehp} `{hp}`  {eatt} `{strstat}`  {epr} `{prstat}`\n'
                                                   f'{ewp} `{wpstat}`  {emag} `{magstat}`  {emr} `{mrstat}`')
        custom_embed.set_thumbnail(url=imageurl)
        custom_embed.set_footer(text=f'Created {month} {year}')
        await ctx.send(embed=custom_embed)


def setup(bot):
    bot.add_cog(OwO(bot))
    bot.add_cog(Taco(bot))