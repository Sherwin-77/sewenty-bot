# bot.py
import asyncio
from datetime import datetime
from glob import glob
from io import BytesIO
import json
import logging
from os import getenv
from os.path import relpath
import random
from traceback import format_exception
from typing import Union

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import motor.motor_asyncio
import psutil
from psutil._common import bytes2human

from utils.paginators import SimplePages, EmbedSource

USE_PSQL = False

__version__ = "2.2.3"

load_dotenv()  # in case we use .env in future

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s:%(name)s: %(message)s")
logger = logging.getLogger("main")


class NewHelpCommand(commands.MinimalHelpCommand):
    def __init__(self, **options):
        super().__init__(**options)
        self.no_category = "Other Command"

    # TODO: Add send_bot_help overriding

    async def send_pages(self):
        if len(self.paginator.pages) < 2:
            destination = self.get_destination()
            await destination.send(embed=discord.Embed(title="Help", description=self.paginator.pages[0],
                                                       color=discord.Colour.random()))
        else:
            ctx = self.context
            menu = SimplePages(source=EmbedSource(self.paginator.pages, 1, "Help", lambda pg: pg))
            await menu.start(ctx)


# noinspection SpellCheckingInspection
class SewentyBot(commands.Bot):
    # TODO: Implement psql

    disabled_app_command = {"kingdom show", "kingdom upgrade", "kingdom train",
                            "kingdom collect", "kingdom attack"}

    TOKEN = getenv("DISCORD_TOKEN")
    EMAILS = getenv("EMAIL")
    PASSWORDS = getenv("PASSWORD")
    SECOND_EMAIL = getenv("NEXT_EMAIL")
    SECOND_PASSWORD = getenv("NEXT_PASSWORD")
    CPDB_NAME = getenv("CPDB_NAME")
    DB_NAME = getenv("DB_NAME")
    MANGO_URL = f"mongodb+srv://{EMAILS}:{PASSWORDS}@{DB_NAME}.mongodb.net/test"
    CP_URL = f"mongodb+srv://{SECOND_EMAIL}:{SECOND_PASSWORD}@{CPDB_NAME}.mongodb.net/Hakibot"
    PSQL_USER = getenv("PSQL_USER")
    PSQL_PASSWORD = getenv("PSQL_PASSWORD")

    # Test db
    # MANGO_URL = f"mongodb+srv://{EMAILS}:{PASSWORDS}@cluster0.kvwdz.mongodb.net/test"

    def __init__(self):
        intents = discord.Intents.all()  # ah yes
        super().__init__(
            case_insensitive=True,
            command_prefix=commands.when_mentioned_or("s!"),  # type: ignore
            description="Sewenty bot written in python",
            intents=intents,
            status=discord.Status.idle,
            activity=discord.Game(name="s!help")
        )

        self.TEST_MODE = False
        self.help_command = NewHelpCommand()
        self._BotBase__cogs = commands.core._CaseInsensitiveDict()  # protected member warning be like
        self.launch_timestamp = int(datetime.now().timestamp())
        self.owner = None
        self.banned_user = set()
        self.last_stack = []
        self.last_date = None
        self.afk_message = "Ded or work or college >:("

        self.TRIGGER_RESPONSE = {"hakid": ["<:hikablameOwO:851556784380313631>",
                                           "<:hikanoplsOwO:804522598289375232>"],
                                 "shifud": ["<a:BowingPandas:771010441324920853>",
                                            "<:speechlessOwO:793026526911135744>",
                                            ">.<"],
                                 "meo": "<a:catMIAOwO:782034693905186816>",
                                 "radishh": ["<a:blossomradish:812889706249453618>",
                                             "<a:radishblossom:802357456885383198>"],
                                 "naed": "<a:emoji3:776775391154798593>",
                                 "test ajg": "<:wurk:858721776770744320>",
                                 "xnurag": "⚠ **|** Please complete your captcha to verify that you are human! (9/6) "
                                           "<a:pandasmackOwO:799955371074519041>",
                                 "vinwuv": "osu! when",
                                 "invad": "When",
                                 "thonk": "<:PaulThink:770782702973878283>"}

        # we define this later
        self.pool = None
        self.session = None
        self.DB = None
        self.CP_DB = None
        self.LXV_DB = None
        self.GAME_COLLECTION = None
        self.guild_prefix = dict()
        self.allowed_track_channel = dict()
        self.cached_soldier_data = []

    async def setup_hook(self) -> None:
        if self.TEST_MODE:
            logger.warning("Test mode turned on. Consider turning off before production")
        self.session = aiohttp.ClientSession()

        cluster = motor.motor_asyncio.AsyncIOMotorClient(self.MANGO_URL)
        cluster1 = motor.motor_asyncio.AsyncIOMotorClient(self.CP_URL)
        app = await self.application_info()
        logger.info("Aiohttp session and database connected")

        self.owner = app.owner
        self.DB = cluster["Data"]
        self.CP_DB = cluster1["Hakibot"]
        self.LXV_DB = cluster1["lxv"]
        self.GAME_COLLECTION = cluster["game"]["data"]

        for file in glob(r"extensions/*.py"):
            module_name = relpath(file).replace("\\", '.').replace('/', '.')[:-3]
            await self.load_extension(module_name)
        await self.get_soldier_cache()
        form = {"_id": "prefix"}
        result = await self.DB["bot"].find_one(form)
        if result:
            self.guild_prefix = result["prefix_list"]
        logger.info("Prefix loaded")
        form = {"_id": "allowed_channel"}
        result = await self.DB["bot"].find_one(form)
        if not result:
            logger.warning("No channel to be refreshed")
        else:
            new = result["channel_list"]
            self.allowed_track_channel = new
        logger.info("Cache loaded")

        # await self.load_extension("experiment")  # for experimenting
        await self.load_extension("blockingcog")
        await self.load_extension("jishaku")
        logger.info("Module loaded")

    async def get_prefix(self, message: discord.Message, /):
        """|coro|

        Retrieves the prefix the bot is listening to
        with the message as a context.

        .. versionchanged:: 2.0

            ``message`` parameter is now positional-only.

        Parameters
        -----------
        message: :class:`discord.Message`
            The message context to get the prefix of.

        Returns
        --------
        Union[List[:class:`str`], :class:`str`]
            A list of prefixes or a single prefix that the bot is
            listening for.
        """
        if self.TEST_MODE:
            return ["test!"]
        ret = await super().get_prefix(message)
        if f"guild{message.guild.id}" in self.guild_prefix:
            ret.append(self.guild_prefix[f"guild{message.guild.id}"])
        return ret

    async def close(self) -> None:
        await self.session.close()
        await super().close()

    async def main(self) -> None:
        await self.start(self.TOKEN)

    async def send_owner(self, message=None, **kwargs) -> None:
        channel = await self.owner.create_dm()
        await channel.send(message, **kwargs)

    async def get_soldier_cache(self) -> None:
        if not USE_PSQL:
            return
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                self.cached_soldier_data = await conn.fetch("SELECT * FROM soldier_info")

    def blocking_stack(self, traceback) -> None:
        logger.warning("Blocking code detected. You also can check from s!laststack")
        self.last_stack = traceback
        self.last_date = datetime.utcnow()


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

    @bot.command(hidden=True)
    @commands.is_owner()
    async def laststack(ctx):
        if not bot.last_stack:
            return await ctx.send("No blocking code detected")
        output = ''.join(bot.last_stack)
        if len(output) > 1500:
            buffer = BytesIO(output.encode("utf-8"))
            file = discord.File(buffer, filename="log.txt")
            await ctx.send(f"Blocked at {bot.last_date}", file=file)
        else:
            custom_embed = discord.Embed(description=output, color=discord.Colour.red())
            custom_embed.set_footer(text=f"Blocked at {bot.last_date}")
            await ctx.send(embed=custom_embed)

    @bot.command(hidden=True)
    @commands.is_owner()
    async def refresh(ctx):
        """
        Nothing Special
        """
        original = await ctx.send("Refreshing <a:discordloading:792012369168957450>")
        await bot.get_soldier_cache()
        await original.edit(content="Done <:wurk:858721776770744320>")

    @bot.command(hidden=True)
    @commands.is_owner()
    async def sql(ctx, *, query):
        if not USE_PSQL:
            return await ctx.reply("Psql disabled", mention_author=False)
        async with bot.pool.acquire() as conn:
            async with conn.transaction():
                value = await conn.execute(query)
        await ctx.send(embed=discord.Embed(title="Result",
                                           description=value,
                                           color=discord.Colour.random()))

    @sql.error
    async def sql_on_error(ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            return await ctx.reply(f"Failed to fetch: {type(error.original)} {error.original}", mention_author=False)
        await ctx.reply(f"Failed to fetch: {type(error)} {error}", mention_author=False)

    @bot.command(hidden=True)
    @commands.is_owner()
    async def catch(ctx: commands.Context):
        ref = ctx.message.reference
        if ref is None or not isinstance(ref.resolved, discord.Message):
            return await ctx.reply("Where message", mention_author=False)
        message = ref.resolved
        if message.embeds:
            output = json.dumps(message.embeds[0].to_dict(), indent='\t')
            custom_embed = discord.Embed(description=f"```{output}\n```",
                                         color=discord.Colour.random())
            await ctx.send(embed=custom_embed)
        elif message.stickers:
            custom_embed = discord.Embed(description='\n'.join([f"{i}. {v.id} - {v.name}.{v.format.file_extension} "
                                                                f"({v.url})"
                                                                for i, v in enumerate(message.stickers, start=1)]))
            await ctx.send(embed=custom_embed)
        else:
            await ctx.send("Unable to catch fish")

    # noinspection SpellCheckingInspection
    @bot.command(hidden=True)
    @commands.is_owner()
    async def ban(ctx, user: discord.User):
        """
        Not to be confused with guild ban, this bans user from bot
        """

        if user.id in bot.banned_user:
            bot.banned_user.remove(user.id)
            return await ctx.send(f"{user.display_name} un gone <a:menheraball:810779283692978209>")
        bot.banned_user.add(user.id)
        await ctx.send(f"{user.display_name} gone <:kenasandal:805028596581269524>")

    @bot.command(hidden=True)
    @commands.is_owner()
    async def dm(ctx, user: discord.User, *, text="Test"):
        channel = await user.create_dm()
        await channel.send(text)
        await ctx.message.add_reaction('👍')

    @dm.error
    async def dm_error(ctx, error):
        await ctx.reply(f"Failed to dm: `{error}`\n"
                        f"`{type(error)}`")

    @bot.command(hidden=True)
    @commands.is_owner()
    async def switch(ctx: commands.Context, command: bot.get_command):
        """
        Disable command-
        """
        if command == ctx.command:
            return await ctx.send("You can't disable this")
        if not command.enabled:
            command.enabled = True
            return await ctx.send("Switch to enabled")
        command.enabled = False
        return await ctx.send("Switch to disabled")

    @bot.command(hidden=True)
    @commands.is_owner()
    async def send(ctx, channel: discord.TextChannel, *, text="Test"):
        await channel.send(text)
        await ctx.message.add_reaction('👍')

    @send.error
    async def send_error(ctx, error):
        await ctx.reply(f"Failed to send: `{error}`\n"
                        f"`{type(error)}`")

    # Note that channel id in dict always str
    @bot.command(name="allowchannel", hidden=True)
    @commands.is_owner()
    async def allow_channel(ctx: commands.Context, channel_id: Union[discord.TextChannel, int], boss_mode=False):
        """
        Allow tracking anigame rng
        Work for owner only
        """
        collection = bot.DB["bot"]
        if isinstance(channel_id, discord.TextChannel):
            channel_id = channel_id.id
        channel_id = str(channel_id)
        form = {"_id": "allowed_channel"}
        result = await collection.find_one(form)
        if not result:
            result = {channel_id: boss_mode}
            await collection.insert_one(form, {"$set": {"channel_list": result}})
            return await ctx.send("No channel list detected, creating one..")
        new = result["channel_list"]
        if channel_id in new:
            new.pop(channel_id)
            bot.allowed_track_channel.pop(channel_id)
            collection.update_one(form, {"$set": {"channel_list": new}})
            return await ctx.send("Disabled!")
        new.update({channel_id: boss_mode})
        bot.allowed_track_channel.update({channel_id: boss_mode})
        collection.update_one(form, {"$set": {"channel_list": new}})
        await ctx.send("Enabled!")

    @bot.command()
    @commands.cooldown(rate=1, per=3.0, type=commands.BucketType.user)
    async def stat(ctx):
        """
        Show bot stats
        """
        count_guild = len(bot.guilds)
        is_owner = await ctx.bot.is_owner(ctx.author)
        if is_owner:
            await ctx.send(f"Hello {ctx.author.mention}", delete_after=5)
        virtual_memory = psutil.virtual_memory()
        memory_detail = []
        for name in virtual_memory._fields:
            value = getattr(virtual_memory, name)
            if name != "percent":
                value = bytes2human(value)
            else:
                value = f"{value} %"
            memory_detail.append(f"{name.capitalize()}: {value}")

        custom_embed = discord.Embed(title="Bot Stats",
                                     description=f"Uptime: <t:{bot.launch_timestamp}:R>\n"
                                                 f"Total Servers: {count_guild}\n"
                                                 f"Bot Ver: {__version__}\n"
                                                 f"CPU usage: {psutil.cpu_percent(1)}%\n"
                                                 f"Ping: "
                                                 f"{round(bot.latency * 1000)} ms\n"
                                                 f"Running in **"
                                                 f"{'normal' if not bot.TEST_MODE else 'Test'}** mode ",
                                     color=discord.Colour.random())
        custom_embed.add_field(name="Memory", value='\n'.join(memory_detail))
        await ctx.send(embed=custom_embed)

    @bot.event
    async def on_message(message: discord.Message):
        userid = message.author.id
        if message.author.bot:
            return

        if userid in bot.banned_user:
            return

        if message.guild is None:
            channel = bot.get_channel(784707657344221215)
            dm_embed = discord.Embed(description=message.content)
            dm_embed.set_author(name=message.author.name, icon_url=message.author.avatar)
            dm_embed.set_footer(text=message.author.id)
            return await channel.send(embed=dm_embed)

        if bot.TEST_MODE:
            return await bot.process_commands(message)

        if "inva" in message.content.lower():
            await bot.send_owner(f"Mentioned 'inva' at <#{message.channel.id}> **Guild** {message.guild.name}\n"
                                 f"**By:** {message.author} ({message.author.id})\n"
                                 f"**Jump:** {message.jump_url}\n"
                                 f"**Full:**\n"
                                 f"{message.content}")

        guild_id = message.guild.id
        if guild_id == 714152739252338749:
            low_msg = message.content.lower()

            for u in message.mentions:
                if (
                        u.id == bot.owner.id
                        and (u.status == discord.Status.idle
                             or u.status == discord.Status.dnd
                             or u.status == discord.Status.offline)
                        and bot.afk_message is not None
                ):
                    await message.reply(f"<a:running:791350508375900190> **Owner AFK:** {bot.afk_message}",
                                        mention_author=False, allowed_mentions=discord.AllowedMentions.none())

            if low_msg in {"osana", "mira"}:
                if userid in {436376194166816770, 532912006114836482}:
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
        if bot.TEST_MODE:
            return
        if before.author.id == 571027211407196161 and str(before.channel.id) in bot.allowed_track_channel:
            catch_ = after.embeds
            if not catch_:
                return
            processed = catch_[-1].to_dict()
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
                    or "blinded by the smoke" in message.split('\n')[2]
            ):
                message = message.replace("<:ARROW:698301107419611186>", ":arrow_right: ")
                custom_embed = discord.Embed(title=message.split('[')[1].split(']')[0],
                                             description=message.split('\n')[1] + '\n' + message.split('\n')[2],
                                             color=discord.Colour.blue())
                custom_embed.set_footer(text="psst. If you want this tracker, DM/tell invaliduser77")
                await after.channel.send(embed=custom_embed)

    @bot.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.errors.CommandNotFound):
            return
        if isinstance(error, app_commands.errors.CheckFailure):
            return await interaction.response.send_message("You can't use this command or command on maintenance")
        output = ''.join(format_exception(type(error), error, error.__traceback__))
        if len(output) > 1500:
            buffer = BytesIO(output.encode("utf-8"))
            file = discord.File(buffer, filename="log.txt")
            await bot.send_owner(f"Uncaught error in channel <#{interaction.channel.id}> "
                                 f"command `{interaction.command}`",
                                 file=file)
        else:
            custom_embed = discord.Embed(description=f"Uncaught error in channel <#{interaction.channel.id}> "
                                                     f"command {interaction.command}\n"
                                                     f"```py\n{output}\n```",
                                         color=discord.Colour.red())
            await bot.send_owner(embed=custom_embed)

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.errors.CommandNotFound) or hasattr(ctx.command, "on_error"):
            return
        if isinstance(error, commands.errors.DisabledCommand):
            return await ctx.reply("This command is disabled or under maintenance <:speechlessOwO:793026526911135744>",
                                   mention_author=False)
        if isinstance(error, commands.errors.CheckFailure):
            return await ctx.reply("You are not allowed to use this command",
                                   mention_author=False)
        if isinstance(error, commands.errors.CommandOnCooldown):
            return await ctx.reply(f"{error} <:angeryV2:810860324248616960>",
                                   mention_author=False, delete_after=error.retry_after)
        if (
                isinstance(error, commands.errors.NotOwner)
                or isinstance(error, discord.errors.Forbidden)
                or isinstance(error, commands.errors.BadArgument)
                or isinstance(error, commands.errors.MissingRequiredArgument)
        ):
            return await ctx.reply(error, mention_author=False)
        if isinstance(error, commands.errors.UserNotFound):
            return await ctx.reply("User not found", mention_author=False)
        output = ''.join(format_exception(type(error), error, error.__traceback__))
        if len(output) > 1500:
            buffer = BytesIO(output.encode("utf-8"))
            file = discord.File(buffer, filename="log.txt")
            await bot.send_owner(f"Uncaught error in channel <#{ctx.channel.id}> command `{ctx.command}`", file=file)
        else:
            custom_embed = discord.Embed(description=f"Uncaught error in channel <#{ctx.channel.id}> "
                                                     f"command {ctx.command}\n"
                                                     f"```py\n{output}\n```",
                                         color=discord.Colour.red())
            await bot.send_owner(embed=custom_embed)

    asyncio.run(bot.main())


if __name__ == '__main__':
    main()
