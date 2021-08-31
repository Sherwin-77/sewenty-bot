# bot.py
import asyncio
import random
from datetime import datetime
import os
import discord
from discord_slash import SlashCommand
from discord.ext import commands
from pymongo import MongoClient

token = os.getenv('DISCORD_TOKEN')
emails = os.getenv('EMAIL')
passwords = os.getenv('PASSWORD')
intents = discord.Intents.default()
bot = commands.Bot(command_prefix=commands.when_mentioned_or('s!'), intents=intents)
slash = SlashCommand(client=bot, sync_commands=True)
launchTime = int(datetime.now().timestamp())

# cooldown variable
cooldownList = {}
cooldownList1 = {}
allowed_track_channel = {}
emolist = ['<a:pauldance:745965072349659217>', '<a:kittyhyper:742702283287953409>', '<a:yesyess:757119792044965898>',
           '<a:WRhyperrun:757120121276858441>', '<a:1_kannanom:757119200530792538>',
           '<a:discordloading:792012369168957450>',
           '<a:miwk:757468521553723592>', '<a:yessyes:757506011270479902>',
           '<a:bunhide:757561252691050576>', '<a:pandaclap:760744517824806913>',
           '<a:bunStubbornbaby:773332023111974982>',
           '<a:nyaHyperspin:796349061439291392>', '<a:kittyreversedswish:796748963957047407>',
           '<a:kittyconfusedswish:796745579581407232>']

mangourl = f'mongodb+srv://{emails}:{passwords}@clusterdiscord.8dm0p.mongodb.net/test'
cluster = MongoClient(mangourl)
db = cluster["Data"]
collection = db["userdata"]


class NewHelpName(commands.MinimalHelpCommand):
    def __init__(self, **options):
        super().__init__(**options)
        self.no_category = 'Other Command'

    async def send_pages(self):
        randnum = random.randint(0, 16777215)
        destination = self.get_destination()
        for page in self.paginator.pages:
            emby = discord.Embed(title='Help', description=page, color=randnum)
            await destination.send(embed=emby)


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to discord!')
    await bot.change_presence(status=discord.Status.idle,
                              activity=discord.Activity(type=discord.ActivityType.listening, name='s!help'))


@slash.slash(name="when", description="when")
async def when(ctx):
    list_of_when = ["when", "WHEN", "wHeN", "kapan", "imagine when", " when when"]
    await ctx.send(random.choice(list_of_when))


@bot.command(name='dm', hidden=True)
async def diem(ctx, userid, *, text='Test'):
    if ctx.author.id == 436376194166816770:
        try:
            channel = await bot.fetch_user(int(userid))
            channel1 = await channel.create_dm()
            await channel1.send(text)
        except Exception as e:
            await ctx.send(e)
        return
    await ctx.send('Hoho you are expecting dm works for you. But its only me')


@bot.command(name='stat', help="show bot stat")
async def stats(ctx):
    count_guild = len(bot.guilds)
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        await ctx.send(f'Hello {ctx.author.mention}', delete_after=5)
    custom_embed = discord.Embed(title='Bot Stats',
                                 description=f'Uptime: <t:{launchTime}:R>\nTotal Servers: {count_guild}\nBot Ver: 1.2 Stable\n'
                                             f'Ping: '
                                             f'{round(bot.latency * 1000)} ms')
    await ctx.send(embed=custom_embed)


# Note that channel id in dict always str

@bot.command(name="allowchannel", hidden=True, help="allow tracking anigame in channel")
async def allow(ctx, to_grant: discord.TextChannel, boss_mode=False):
    if ctx.author.id != 436376194166816770:
        return
    channel_id = str(to_grant.id)
    form = {"_id": "allowed_channel"}
    result = collection.find_one(form)
    if not result:
        result = {channel_id: boss_mode}
        collection.insert_one(form, {"$set": {"channel_list": result}})
        await ctx.send("No channel list detected, creating one..")
        return
    new = result["channel_list"]
    if channel_id in new:
        new.pop(channel_id)
        allowed_track_channel.pop(channel_id)
        collection.update_one(form, {"$set": {"channel_list": new}})
        await ctx.send("Disabled!")
        return
    new.update({channel_id: boss_mode})
    allowed_track_channel.update({channel_id: boss_mode})
    collection.update_one(form, {"$set": {"channel_list": new}})
    await ctx.send("Enabled!")


@bot.command(name="refresh", hidden=True, help="refresh local enabled channel")
async def cache(ctx):
    global allowed_track_channel
    form = {"_id": "allowed_channel"}
    result = collection.find_one(form)
    if not result:
        await ctx.send("Nothing to refresh!")
    original = await ctx.send("Refreshing <a:discordloading:792012369168957450>")
    new = result["channel_list"]
    allowed_track_channel = new
    await original.edit(content="Done <:wurk:858721776770744320>")


async def owob(message, userid, user1):
    form = {"_id": userid}
    user = collection.find(form)
    for result in user:
        user = result["param"]
    if (user == 2 or user == 3) and str(userid) not in cooldownList:
        cooldownList.update({str(userid): True})
        result = random.choice(emolist)
        await asyncio.sleep(14)
        await message.channel.send(
            f'{user1.mention} `owo battle` cooldown has passed {result}',
            delete_after=5)
        cooldownList.pop(str(userid))
    else:
        return


async def owoh(message, userid, user1):
    form = {"_id": userid}
    user = collection.find(form)
    for result in user:
        user = result["param"]
    if (user == 1 or user == 2) and str(userid) not in cooldownList1:
        cooldownList1.update({str(userid): True})
        result = random.choice(emolist)
        await asyncio.sleep(14)
        await message.channel.send(
            f'{user1.mention} `owo hunt` cooldown has passed {result}', delete_after=5)
        cooldownList1.pop(str(userid))
    else:
        return


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.reply("Looks like you don't have the permission: " + str(error), mention_author=False)


@bot.event
async def on_message(message):
    user1 = message.author
    userid = message.author.id
    if message.author.bot and userid != 555955826880413696:
        return
    if message.guild is None:
        channel = bot.get_channel(784707657344221215)
        dmbed = discord.Embed(description=message.content)
        dmbed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
        dmbed.set_footer(text=message.author.id)
        await channel.send(embed=dmbed)
        return
    guildid = message.guild.id
    form = {"_id": guildid}
    formuser = {"_id": userid}
    if collection.count_documents(form) != 0:
        user = collection.find_one(form)
        oprefix = user["owoprefix"]
        if collection.count_documents(formuser) != 0:
            if (message.content.lower()).replace(' ', '') == 'owob' \
                    or (message.content.lower()).replace(' ', '') == f'{str(oprefix)}b' \
                    or (message.content.lower()).replace(' ', '') == 'owobattle' \
                    or (message.content.lower()).replace(' ', '') == f'{str(oprefix)}battle':
                await owob(message, userid, user1)
            elif (message.content.lower()).replace(' ', '') == 'owoh' \
                    or (message.content.lower()).replace(' ', '') == f'{str(oprefix)}h' \
                    or (message.content.lower()).replace(' ', '') == 'owohunt' \
                    or (message.content.lower()).replace(' ', '') == f'{str(oprefix)}hunt':
                await owoh(message, userid, user1)
    else:
        if collection.count_documents(formuser) != 0:
            if (message.content.lower()).replace(' ', '') == 'owob':
                await owob(message, userid, user1)
            elif (message.content.lower()).replace(' ', '') == 'owoh':
                await owoh(message, userid, user1)
    if guildid == 714152739252338749:
        list_of_name = ['invalid-user', 'Hakiobo', '*Anim', 'BloomJr', 'scratchmario123', 'Osana', 'Yeziest']
        try:
            if message.author.id == 555955826880413696 and message.content.split('**')[1] in list_of_name:
                if '<:Apple:697940429668089867>' in message.content:
                    parsed = message.content.split('**')[3]
                    lt = ['first', 'second', 'third', 'fourth', 'fifth']
                    result = 'apple'[lt.index(parsed)]
                    await message.channel.send(f'Answer: **{result}** <:PaulThinkOwO:770782702973878283>', delete_after=10)
                    return
                elif '<:Banana:697940429483540522>' in message.content:
                    parsed = message.content.split('**')[3]
                    lt = ['first', 'second', 'third', 'fourth', 'fifth', 'sixth']
                    result = 'banana'[lt.index(parsed)]
                    await message.channel.send(f'Answer: **{result}** <:PaulThinkOwO:770782702973878283>', delete_after=10)
                    return
                elif 'casino' in message.content:
                    result = 'idk'
                    if ':four_leaf_clover:' in message.content:
                        if '**FOUR LEAF CLOVER**' in message.content:
                            result = 'Yes'
                        else:
                            result = 'No'
                    elif ':game_die:' in message.content:
                        if '**DICE**' in message.content:
                            result = 'Yes'
                        else:
                            result = 'No'
                    elif ':gift:' in message.content:
                        if '**GIFT**' in message.content:
                            result = 'Yes'
                        else:
                            result = 'No'
                    elif '<:coin:541384484201693185>' in message.content:
                        if '**COIN**' in message.content:
                            result = 'Yes'
                        else:
                            result = 'No'
                    elif ':gem:' in message.content:
                        if '**DIAMOND**' in message.content:
                            result = 'Yes'
                        else:
                            result = 'No'
                    await message.channel.send(f'Answer: **{result}** <:PaulThinkOwO:770782702973878283>', delete_after=10)
                    return
                elif 'forest' in message.content:
                    counter = 0
                    wl = message.content.split('\n')[1].split(':')
                    for x in range(1, 10, 2):
                        if wl[x] == message.content.split('\n')[2].split(':')[1]:
                            counter += 1
                    await message.channel.send(f'Answer: **{counter}** <:PaulThinkOwO:770782702973878283>', delete_after=10)
                    return
                elif 'river' in message.content:
                    if ':normiefish:' in message.content.lower():
                        result = 1
                    elif ':goldenfish:' in message.content.lower():
                        result = 2
                    else:
                        result = 3
                    await message.channel.send(f'Answer: **{result}** <:PaulThinkOwO:770782702973878283>', delete_after=10)
                    return
                elif 'training in the mine' in message.content:
                    await message.channel.send('Answer: idk smh <:PaulThinkOwO:770782702973878283>', delete_after=3)
                    return
            if message.author.bot:
                return
        except IndexError:
            return
        if message.content.lower() == 'hakid':
            await message.channel.send('Bot programmer <a:PaulLeavingOwO:745964937305784375>')
        if message.content.lower() == 'osana':
            if userid == 436376194166816770 or userid == 532912006114836482:
                await message.channel.send('<a:bun:743740123094450217>')
            else:
                await message.channel.send('<a:gimme:751779307688296498>')
        if message.content.lower() == 'shifud':
            await message.channel.send('<a:BowingPandas:771010441324920853>')
        if message.content.lower() == 'meo':
            await message.channel.send('<a:catMIAOwO:782034693905186816>')
        if message.content.lower() == 'naed':
            await message.channel.send('<a:emoji3:776775391154798593>')
        if message.content.lower() == 'radishh':
            await message.channel.send('<a:radishblossom:802357456885383198>')
    await bot.process_commands(message)


@bot.event
async def on_message_edit(before, after):
    if before.author.id == 571027211407196161 and str(before.channel.id) in allowed_track_channel:
        catch = after.embeds
        processed = {}
        for x in catch:
            processed = x.to_dict()
        try:
            message = processed["fields"][0]["value"]
        except KeyError:
            return
        if (("CRITICAL HIT" in message.split('\n')[2] and (allowed_track_channel[str(after.channel.id)] or
                                                           "Rage Mode" not in message)) or
                "managed to evade" in message.split('\n')[2] or "fortunately it resisted" in message.split('\n')[2] or
                "uses Lucky Coin" in message.split('\n')[2] or "uses Unlucky Coin" in message.split('\n')[2]):
            message = message.replace("<:ARROW:698301107419611186>", ":arrow_right: ")
            custom_embed = discord.Embed(title=message.split('[')[1].split(']')[0],
                                         description=message.split('\n')[1] + '\n' + message.split('\n')[2])
            await after.channel.send(embed=custom_embed)

bot.load_extension("general")
bot.load_extension("dbcommand")
bot.load_extension("helper")
bot.load_extension("game")
bot.load_extension("misc")
bot.help_command = NewHelpName()
bot.run(token)
