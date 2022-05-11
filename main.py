# bot.py
import asyncio
from datetime import datetime
from glob import glob
from os import getenv
from os.path import relpath
import random
from traceback import format_exception

import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv
import motor.motor_asyncio

load_dotenv()  # in case we use .env in future

COMMANDS_FOLDER = r"commands/"

TOKEN = getenv("DISCORD_TOKEN")
EMAILS = getenv("EMAIL")
PASSWORDS = getenv("PASSWORD")
SECOND_EMAIL = getenv("NEXT_EMAIL")
SECOND_PASSWORD = getenv("NEXT_PASSWORD")
CPDB_NAME = getenv("CPDB_NAME")
DB_NAME = getenv("DB_NAME")

# Test db
# MANGO_URL = f"mongodb+srv://{EMAILS}:{PASSWORDS}@cluster0.kvwdz.mongodb.net/test"

MANGO_URL = f"mongodb+srv://{EMAILS}:{PASSWORDS}@{DB_NAME}.mongodb.net/test"
CLUSTER = motor.motor_asyncio.AsyncIOMotorClient(MANGO_URL)
DB = CLUSTER["Data"]
COLLECTION = DB["userdata"]

CP_URL = f"mongodb+srv://{SECOND_EMAIL}:{SECOND_PASSWORD}@{CPDB_NAME}.mongodb.net/Hakibot"
CP_CLUSTER = motor.motor_asyncio.AsyncIOMotorClient(CP_URL)
CP_DB = CP_CLUSTER["Hakibot"]

intents = discord.Intents.all()  # ah yes
bot = commands.Bot(command_prefix=commands.when_mentioned_or("s!"),
                   case_insensitive=True,
                   intents=intents,
                   status=discord.Status.idle,
                   activity=discord.Game(name="s!help")
                   )

launchTime = int(datetime.now().timestamp())

TRIGGER_RESPONSE = {"hakid": ["<:hikablameOwO:851556784380313631>",
                              "<:hikanoplsOwO:804522598289375232>"],
                    "shifud": ["<a:BowingPandas:771010441324920853>",
                               "<:speechlessOwO:793026526911135744>"],
                    "meo": "<a:catMIAOwO:782034693905186816>",
                    "radishh": ["<a:blossomradish:812889706249453618>",
                                "<a:blossomradish:812889706249453618>"],
                    "naed": "<a:emoji3:776775391154798593>",
                    "test ajg": "<:wurk:858721776770744320>",
                    "xnurag": "⚠ **|** Please complete your captcha to verify that you are human! (9/6) "
                              "<a:pandasmackOwO:799955371074519041>"}

allowed_track_channel = {}


class NewHelpCommand(commands.MinimalHelpCommand):
    def __init__(self, **options):
        super().__init__(**options)
        self.no_category = 'Other Command'

    async def send_pages(self):
        rand_num = random.randint(0, 16777215)
        destination = self.get_destination()
        for page in self.paginator.pages:
            help_embed = discord.Embed(title="Help", description=page, color=rand_num)
            await destination.send(embed=help_embed)


@bot.event
async def on_ready():
    global allowed_track_channel
    print(f"{bot.user.name} has connected to discord!")
    form = {"_id": "allowed_channel"}
    result = await COLLECTION.find_one(form)
    if not result:
        print("No channel to be refreshed")
    else:
        new = result["channel_list"]
        allowed_track_channel = new
        print("Refresh channel done!")


@bot.tree.context_menu(name="Banner")
async def search_banner(interaction: discord.Interaction, member: discord.Member):
    embed = discord.Embed(title="Banner")
    embed.set_author(name=member.display_name, icon_url=member.display_avatar)
    member = await bot.fetch_user(member.id)
    banner_url = member.banner
    if not banner_url:
        banner_url = "https://c4.wallpaperflare.com/wallpaper/" \
                     "357/645/211/easter-island-chile-starry-night-statue-wallpaper-preview.jpg"
    embed.set_image(url=banner_url)
    await interaction.response.send_message(embed=embed)


@bot.tree.context_menu(name="Ajg", guild=discord.Object(id=714152739252338749))
async def ajg(interaction: discord.Interaction, user: discord.User):
    await interaction.response.send_message(f"Ajg 👉 {user.mention}")


@bot.command(name="dm", hidden=True)
async def dm_user(ctx, userid: int, *, text="Test"):
    if ctx.author.id == 436376194166816770:
        user = await bot.fetch_user(userid)
        channel = await user.create_dm()
        await channel.send(text)
    else:
        await ctx.send("Hoho you are expecting dm works for you. But its only me")


@dm_user.error
async def dm_error(ctx, error):
    await ctx.reply(f"Failed to dm: {error}\n"
                    f"`{type(error)}`")


@bot.command()
@commands.cooldown(rate=1, per=3.0)
async def stat(ctx):
    """
    Show bot stats
    """
    count_guild = len(bot.guilds)
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        await ctx.send(f"Hello {ctx.author.mention}", delete_after=5)
    custom_embed = discord.Embed(title='Bot Stats',
                                 description=f"Uptime: <t:{launchTime}:R>\n"
                                             f"Total Servers: {count_guild}\n"
                                             f"Bot Ver: 1.3 Beta\n"
                                             f"Ping: "
                                             f"{round(bot.latency * 1000)} ms",
                                 color=discord.Colour.random())
    await ctx.send(embed=custom_embed)


# Note that channel id in dict always str

@bot.command(name="allowchannel", hidden=True)
async def allow_channel(ctx, to_grant: discord.TextChannel, boss_mode=False):
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
        dm_embed.set_author(name=message.author.name, icon_url=message.author.avatar)
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
    if isinstance(error, commands.errors.DisabledCommand):
        await ctx.reply("This command is disabled or under maintenance <:speechlessOwO:793026526911135744>",
                        mention_author=False)
        return
    if isinstance(error, commands.errors.CommandOnCooldown):
        await ctx.reply(f"{error} <:angeryV2:810860324248616960>", mention_author=False, delete_after=error.retry_after)
        return
    if isinstance(error, commands.errors.UserNotFound):
        await ctx.reply("User not found", mention_author=False)
        return
    if isinstance(error, commands.errors.CommandNotFound) or hasattr(ctx.command, 'on_error'):
        return
    owner = await bot.fetch_user(436376194166816770)
    channel = await owner.create_dm()
    output = ''.join(format_exception(type(error), error, error.__traceback__))
    if len(output) > 2000:
        return print(output)
    await channel.send(f"Uncaught error in channel <#{ctx.channel.id}> command `{ctx.command}`\n"
                       f"```py\n"
                       f"{output}```")


async def load_all():
    for file in glob(f"{COMMANDS_FOLDER}*.py"):
        module_name = relpath(file).replace("\\", '.').replace('/', '.')[:-3]
        await bot.load_extension(module_name)
    # await bot.load_extension("experiment")  # for experimenting
    await bot.load_extension("jishaku")
    print("Module loaded")


async def main():
    # in case I forget later, guild only app commands are ajg and custom battle
    bot.help_command = NewHelpCommand()
    bot._BotBase__cogs = commands.core._CaseInsensitiveDict()   # protected member warning be like
    async with aiohttp.ClientSession() as session:
        bot.session = session
        bot.DB = DB
        bot.CP_DB = CP_DB
        bot.GAME_COLLECTION = CLUSTER["game"]["data"]
        await load_all()

        await bot.start(TOKEN)


if __name__ == '__main__':
    asyncio.run(main())
