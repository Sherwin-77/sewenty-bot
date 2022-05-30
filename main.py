# bot.py
import asyncio
from datetime import datetime
from glob import glob
from os import getenv
from os.path import relpath
import random
from traceback import format_exception

import aiohttp
# import asyncpg
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import motor.motor_asyncio

load_dotenv()  # in case we use .env in future

TOKEN = getenv("DISCORD_TOKEN")
EMAILS = getenv("EMAIL")
PASSWORDS = getenv("PASSWORD")
SECOND_EMAIL = getenv("NEXT_EMAIL")
SECOND_PASSWORD = getenv("NEXT_PASSWORD")
CPDB_NAME = getenv("CPDB_NAME")
DB_NAME = getenv("DB_NAME")
# PSQL_USER = getenv("PSQL_USER")
# PSQL_PASSWORD = getenv("PSQL_PASSWORD")

# Test db
# MANGO_URL = f"mongodb+srv://{EMAILS}:{PASSWORDS}@cluster0.kvwdz.mongodb.net/test"

MANGO_URL = f"mongodb+srv://{EMAILS}:{PASSWORDS}@{DB_NAME}.mongodb.net/test"
CP_URL = f"mongodb+srv://{SECOND_EMAIL}:{SECOND_PASSWORD}@{CPDB_NAME}.mongodb.net/Hakibot"


prefixes = ["s!", "S!"]


class NewHelpCommand(commands.MinimalHelpCommand):
    def __init__(self, **options):
        super().__init__(**options)
        self.no_category = "Other Command"

    async def send_pages(self):
        destination = self.get_destination()
        for page in self.paginator.pages:
            help_embed = discord.Embed(title="Help", description=page, color=discord.Colour.random())
            await destination.send(embed=help_embed)


def _prefix_callable(bot_, _):
    bot_id = bot_.user.id
    prefixes.extend([f"<@!{bot_id}> ", f"<@{bot_id}> "])
    return prefixes


# noinspection SpellCheckingInspection
class SewentyBot(commands.Bot):

    disabled_app_command = {"kingdom show", "kingdom upgrade", "kingdom train",
                            "kingdom collect", "kingdom attack"}

    def __init__(self):
        intents = discord.Intents.all()  # ah yes
        super().__init__(case_insensitive=True,
                         command_prefix=_prefix_callable,
                         description="Sewenty bot written in python",
                         intents=intents,
                         status=discord.Status.idle,
                         activity=discord.Game(name="s!help")
                         )

        cluster = motor.motor_asyncio.AsyncIOMotorClient(MANGO_URL)

        self.DB = cluster["Data"]
        self.CP_DB = motor.motor_asyncio.AsyncIOMotorClient(CP_URL)["Hakibot"]
        self.GAME_COLLECTION = cluster["game"]["data"]
        self.help_command = NewHelpCommand()
        self._BotBase__cogs = commands.core._CaseInsensitiveDict()  # protected member warning be like
        self.launch_timestamp = int(datetime.now().timestamp())

        self.TRIGGER_RESPONSE = {"hakid": ["<:hikablameOwO:851556784380313631>",
                                           "<:hikanoplsOwO:804522598289375232>"],
                                 "shifud": ["<a:BowingPandas:771010441324920853>",
                                            "<:speechlessOwO:793026526911135744>"],
                                 "meo": "<a:catMIAOwO:782034693905186816>",
                                 "radishh": ["<a:blossomradish:812889706249453618>",
                                             "<a:radishblossom:802357456885383198>"],
                                 "naed": "<a:emoji3:776775391154798593>",
                                 "test ajg": "<:wurk:858721776770744320>",
                                 "xnurag": "⚠ **|** Please complete your captcha to verify that you are human! (9/6) "
                                           "<a:pandasmackOwO:799955371074519041>"}

        # we define this later
        # self.pool = None
        self.session = None
        # self.cached_soldier_data = []
        self.allowed_track_channel = dict()

    async def setup_hook(self) -> None:
        self.session = aiohttp.ClientSession()

        for file in glob(r"extensions/*.py"):
            module_name = relpath(file).replace("\\", '.').replace('/', '.')[:-3]
            await self.load_extension(module_name)
        # await self.load_extension("experiment")  # for experimenting
        await self.load_extension("jishaku")
        print("Module loaded")

        # await self.get_soldier_cache()
        form = {"_id": "allowed_channel"}
        result = await self.DB["userdata"].find_one(form)
        if not result:
            print("No channel to be refreshed")
        else:
            new = result["channel_list"]
            self.allowed_track_channel = new
        print("Cache loaded")

    async def close(self) -> None:
        await super().close()
        await self.session.close()

    async def main(self) -> None:
        # pool = await asyncpg.create_pool(
        #     database=PSQL_USER,
        #     user=PSQL_USER,
        #     password=PSQL_PASSWORD
        # )
        # async with self, pool:
        #     self.pool: asyncpg.Pool = pool
        await self.start(TOKEN)

    # async def get_soldier_cache(self) -> None:
    #     async with self.pool.acquire() as conn:
    #         async with conn.transaction():
    #             self.cached_soldier_data = await conn.fetch("SELECT * FROM soldier_info")


def slash_is_enabled():
    def wrapper(interaction: discord.Interaction):
        return interaction.command.qualified_name not in SewentyBot.disabled_app_command
    return app_commands.check(wrapper)


def main():
    default_banner_url = getenv("DEFAULT_BANNER_URL")

    bot = SewentyBot()

    # another dirty way to access bot var

    @bot.event
    async def on_ready():
        print(f"{bot.user.name} has connected to discord!")

    @bot.tree.context_menu(name="Banner")
    async def search_banner(interaction: discord.Interaction, member: discord.Member):
        member = await bot.fetch_user(member.id)
        banner_url = member.banner or default_banner_url

        custom_embed = discord.Embed()
        custom_embed.set_author(name=f"{member.display_name}'s banner", icon_url=member.display_avatar)
        custom_embed.set_image(url=banner_url)
        await interaction.response.send_message(embed=custom_embed)

    @bot.tree.context_menu(name="Ajg", guild=discord.Object(id=714152739252338749))
    async def ajg(interaction: discord.Interaction, user: discord.User):
        await interaction.response.send_message(f"Ajg 👉 {user.mention}")

    # @bot.command(hidden=True)
    # async def refresh(ctx):
    #     """
    #     Nothing Special
    #     """
    #     original = await ctx.send("Refreshing <a:discordloading:792012369168957450>")
    #     await bot.get_soldier_cache()
    #     await original.edit(content="Done <:wurk:858721776770744320>")

    # @bot.command(hidden=True)
    # @commands.is_owner()
    # async def sql(ctx, *, query):
    #     async with bot.pool.acquire() as conn:
    #         async with conn.transaction():
    #             value = await conn.execute(query)
    #     await ctx.send(embed=discord.Embed(title="Result",
    #                                        description=value,
    #                                        color=discord.Colour.random()))

    # @sql.error
    # async def sql_on_error(ctx, error):
    #     if isinstance(error, commands.CommandInvokeError):
    #         return await ctx.reply(f"Failed to fetch: {type(error.original)} {error.original}", mention_author=False)
    #     await ctx.reply(f"Failed to fetch: {type(error)} {error}", mention_author=False)

    @bot.command(name="dm", hidden=True)
    @commands.is_owner()
    async def dm_user(ctx, user: discord.User, *, text="Test"):
        channel = await user.create_dm()
        await channel.send(text)
        await ctx.message.add_reaction('👍')

    @dm_user.error
    async def dm_error(ctx, error):
        await ctx.reply(f"Failed to dm: `{error}`\n"
                        f"`{type(error)}`")

    @bot.command()
    @commands.is_owner()
    async def send(ctx, channel: discord.TextChannel, *, text="Test"):
        await channel.send(text)
        await ctx.message.add_reaction('👍')

    @send.error
    async def send_error(ctx, error):
        await ctx.reply(f"Failed to send: `{error}`\n"
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
                                     description=f"Uptime: <t:{bot.launch_timestamp}:R>\n"
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
        collection = bot.DB["userdata"]
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
            bot.allowed_track_channel.pop(channel_id)
            collection.update_one(form, {"$set": {"channel_list": new}})
            await ctx.send("Disabled!")
            return
        new.update({channel_id: boss_mode})
        bot.allowed_track_channel.update({channel_id: boss_mode})
        collection.update_one(form, {"$set": {"channel_list": new}})
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
            if low_msg == "osana":
                if userid == 436376194166816770 or userid == 532912006114836482:
                    await message.channel.send("<a:bun:743740123094450217>")
                else:
                    await message.channel.send("<a:gimme:751779307688296498>")
            if low_msg in bot.TRIGGER_RESPONSE.keys():
                if isinstance(bot.TRIGGER_RESPONSE[low_msg], list):
                    await message.channel.send(random.choice(bot.TRIGGER_RESPONSE[low_msg]))
                else:
                    await message.channel.send(bot.TRIGGER_RESPONSE[low_msg])

        await bot.process_commands(message)

    @bot.event
    async def on_message_edit(before, after):
        if before.author.id == 571027211407196161 and str(before.channel.id) in bot.allowed_track_channel:
            catch = after.embeds
            processed = {}
            for x in catch:
                processed = x.to_dict()
            try:
                message = processed["fields"][0]["value"]
            except KeyError:
                return

            if (
                    (
                            "CRITICAL HIT" in message.split('\n')[2]
                            and (
                                    bot.allowed_track_channel[str(after.channel.id)]
                                    or "Rage Mode" not in message
                            )
                    )
                    or "managed to evade" in message.split('\n')[2]
                    or "fortunately it resisted" in message.split('\n')[2]
                    or "uses Lucky Coin" in message.split('\n')[2]
                    or "uses Unlucky Coin" in message.split('\n')[2]
            ):
                message = message.replace("<:ARROW:698301107419611186>", ":arrow_right: ")
                custom_embed = discord.Embed(title=message.split('[')[1].split(']')[0],
                                             description=message.split('\n')[1] + '\n' + message.split('\n')[2])
                await after.channel.send(embed=custom_embed)

    @bot.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandNotFound) or hasattr(interaction.command, 'on_error'):
            return
        if isinstance(error, app_commands.CheckFailure):
            return await interaction.response.send_message("You can't use this command (probably on maintenance)")
        output = ''.join(format_exception(type(error), error, error.__traceback__))
        if len(output) > 1500:
            return print(output)
        owner = await bot.fetch_user(436376194166816770)
        channel = await owner.create_dm()
        await channel.send(f"Uncaught error in channel <#{interaction.channel.id}> "
                           f"command `{interaction.command.qualified_name}`\n"
                           f"```py\n"
                           f"{output}```")

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.errors.DisabledCommand):
            return await ctx.reply("This command is disabled or under maintenance <:speechlessOwO:793026526911135744>",
                                   mention_author=False)
        if isinstance(error, commands.errors.CommandOnCooldown):
            return await ctx.reply(f"{error} <:angeryV2:810860324248616960>",
                                   mention_author=False, delete_after=error.retry_after)
        if isinstance(error, commands.errors.UserNotFound):
            return await ctx.reply("User not found", mention_author=False)
        if isinstance(error, commands.errors.CommandNotFound) or hasattr(ctx.command, 'on_error'):
            return

        output = ''.join(format_exception(type(error), error, error.__traceback__))
        if len(output) > 1500:
            return print(output)
        owner = await bot.fetch_user(436376194166816770)
        channel = await owner.create_dm()
        await channel.send(f"Uncaught error in channel <#{ctx.channel.id}> command `{ctx.command}`\n"
                           f"```py\n"
                           f"{output}```")

    asyncio.run(bot.main())


if __name__ == '__main__':
    main()
