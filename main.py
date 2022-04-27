# bot.py
import asyncio
import random
from datetime import datetime
import os
import discord
from discord.ext import commands
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('DISCORD_TOKEN')
EMAILS = os.getenv('EMAIL')
PASSWORDS = os.getenv('PASSWORD')
intents = discord.Intents.all()  # ah yes
bot = commands.Bot(command_prefix=commands.when_mentioned_or('s!'), intents=intents)
launchTime = int(datetime.now().timestamp())

TRIGGER_RESPONSE = {"hakid": ["<:hikablameOwO:851556784380313631>",
                              "<:hikanoplsOwO:804522598289375232>"],
                    "shifud": ["<a:BowingPandas:771010441324920853>",
                               "<:speechlessOwO:793026526911135744>"],
                    "meo": "<a:catMIAOwO:782034693905186816>",
                    "radishh": ["<a:blossomradish:812889706249453618>",
                                "<a:blossomradish:812889706249453618>"],
                    "naed": "<a:emoji3:776775391154798593>",
                    "testt ajg": "<:wurk:858721776770744320>",
                    "xnurag": "⚠ **|** Please complete your captcha to verify that you are human! (9/6) "
                              "<a:pandasmackOwO:799955371074519041>"}

allowed_track_channel = {}
EMOJIS = ['<a:pauldance:745965072349659217>', '<a:kittyhyper:742702283287953409>', '<a:yesyess:757119792044965898>',
          '<a:WRhyperrun:757120121276858441>', '<a:1_kannanom:757119200530792538>',
          '<a:discordloading:792012369168957450>',
          '<a:miwk:757468521553723592>', '<a:yessyes:757506011270479902>',
          '<a:bunhide:757561252691050576>', '<a:pandaclap:760744517824806913>',
          '<a:bunStubbornbaby:773332023111974982>',
          '<a:nyaHyperspin:796349061439291392>', '<a:kittyreversedswish:796748963957047407>',
          '<a:kittyconfusedswish:796745579581407232>']

MANGO_URL = f'mongodb+srv://{EMAILS}:{PASSWORDS}@clusterdiscord.8dm0p.mongodb.net/test'
CLUSTER = MongoClient(MANGO_URL)
DB = CLUSTER["Data"]
COLLECTION = DB["userdata"]


class NewHelpName(commands.MinimalHelpCommand):
    def __init__(self, **options):
        super().__init__(**options)
        self.no_category = 'Other Command'

    async def send_pages(self):
        rand_num = random.randint(0, 16777215)
        destination = self.get_destination()
        for page in self.paginator.pages:
            help_embed = discord.Embed(title='Help', description=page, color=rand_num)
            await destination.send(embed=help_embed)


@bot.event
async def on_ready():
    global allowed_track_channel
    print(f'{bot.user.name} has connected to discord!')
    await bot.change_presence(status=discord.Status.idle,
                              activity=discord.Activity(type=discord.ActivityType.listening, name='s!help'))
    form = {"_id": "allowed_channel"}
    result = COLLECTION.find_one(form)
    if not result:
        print("No channel to be refreshed")
    else:
        new = result["channel_list"]
        allowed_track_channel = new
        print("Refresh channel done!")


@bot.command(name='dm', hidden=True)
async def diem(ctx, userid: int, *, text='Test'):
    if ctx.author.id == 436376194166816770:
        user = await bot.fetch_user(userid)
        channel = await user.create_dm()
        await channel.send(text)
    else:
        await ctx.send('Hoho you are expecting dm works for you. But its only me')


@bot.command(name='stat', help="show bot stat")
async def stats(ctx):
    count_guild = len(bot.guilds)
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        await ctx.send(f'Hello {ctx.author.mention}', delete_after=5)
    custom_embed = discord.Embed(title='Bot Stats',
                                 description=f'Uptime: <t:{launchTime}:R>\n'
                                             f'Total Servers: {count_guild}\n'
                                             f'Bot Ver: 1.3 Beta\n'
                                             f'Ping: '
                                             f'{round(bot.latency * 1000)} ms')
    await ctx.send(embed=custom_embed)


# Note that channel id in dict always str

@bot.command(name="allowchannel", hidden=True)
async def allow(ctx, to_grant: discord.TextChannel, boss_mode=False):
    """
    Allow tracking anigame rng
    Work for owner only
    """
    if ctx.author.id != 436376194166816770:
        return
    channel_id = str(to_grant.id)
    form = {"_id": "allowed_channel"}
    result = COLLECTION.find_one(form)
    if not result:
        result = {channel_id: boss_mode}
        COLLECTION.insert_one(form, {"$set": {"channel_list": result}})
        await ctx.send("No channel list detected, creating one..")
        return
    new = result["channel_list"]
    if channel_id in new:
        new.pop(channel_id)
        allowed_track_channel.pop(channel_id)
        COLLECTION.update_one(form, {"$set": {"channel_list": new}})
        await ctx.send("Disabled!")
        return
    new.update({channel_id: boss_mode})
    allowed_track_channel.update({channel_id: boss_mode})
    COLLECTION.update_one(form, {"$set": {"channel_list": new}})
    await ctx.send("Enabled!")


@bot.event
async def on_message(message):
    userid = message.author.id
    if message.author.bot and userid != 555955826880413696:
        return
    if message.guild is None:
        channel = bot.get_channel(784707657344221215)
        dm_embed = discord.Embed(description=message.content)
        dm_embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
        dm_embed.set_footer(text=message.author.id)
        await channel.send(embed=dm_embed)
        return
    guild_id = message.guild.id
    if guild_id == 714152739252338749:
        low_msg = message.content.lower()
        if low_msg == 'osana':
            if userid == 436376194166816770 or userid == 532912006114836482:
                await message.channel.send('<a:bun:743740123094450217>')
            else:
                await message.channel.send('<a:gimme:751779307688296498>')
        if low_msg in TRIGGER_RESPONSE.keys():
            if isinstance(TRIGGER_RESPONSE[low_msg], list):
                await message.channel.send(random.choice(TRIGGER_RESPONSE[low_msg]))
            else:
                await message.channel.send(TRIGGER_RESPONSE[low_msg])

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


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.reply(f"Looks like you don't have the permission: {error}", mention_author=False)
        return
    if isinstance(error, commands.errors.DisabledCommand):
        await ctx.reply("Disabled command <:speechlessOwO:793026526911135744>", mention_author=False)
        return
    if isinstance(error, commands.errors.UserNotFound):
        await ctx.reply("User not found", mention_author=False)
        return
    if isinstance(error, commands.errors.CommandNotFound):
        return
    owner = await bot.fetch_user(436376194166816770)
    channel = await owner.create_dm()
    await channel.send(f"Uncaught error in channel <#{ctx.channel.id}>: `{error}`\n"
                       f"Type: `{type(error)}`")


async def main():
    async with bot:
        await bot.load_extension("general")
        await bot.load_extension("helper")
        await bot.load_extension("misc")
        await bot.load_extension("experiment")
        await bot.load_extension("game")
        await bot.load_extension("jishaku")
        # await bot.load_extension("dbcommand")
        bot.help_command = NewHelpName()
        await bot.start(token)


if __name__ == '__main__':
    asyncio.run(main())
