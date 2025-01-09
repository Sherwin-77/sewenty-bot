# bot.py
import asyncio
import asyncpg
from datetime import datetime
from time import time_ns
from glob import glob
from io import BytesIO
import json

import logging
import logging.config
from os import getenv
from os.path import relpath
import random
from traceback import format_exception
from typing import Optional, Union, Any

import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
import gspread_asyncio
import motor.motor_asyncio
import psutil
from psutil._common import bytes2human

from utils.cache import MessageCache
from utils.paginators import SimplePages, EmbedSource

__version__ = "2.3.0"

load_dotenv()  # in case we use .env in future


def get_service_account_creds():
    creds = Credentials.from_service_account_file("service_accounts/sewentysewen.json")
    scoped = creds.with_scopes(
        [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
    )
    return scoped


logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"simple": {"format": "[{asctime}] [{levelname:^7}] {name}: {message}", "style": "{"}},
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "simple",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "simple",
                "filename": "bot.log",
                "maxBytes": 16 * 1024 * 1024,
                "backupCount": 3,
                "encoding": "utf-8",
            },
        },
        "root": {"level": "INFO", "handlers": ["console", "file"]},
    }
)
logger = logging.getLogger("main")


class NewHelpCommand(commands.MinimalHelpCommand):
    def __init__(self, **options):
        super().__init__(**options)
        self.no_category = "Other Command"

    # TODO: Add send_bot_help overriding

    async def send_pages(self):
        if len(self.paginator.pages) < 2:
            destination = self.get_destination()
            await destination.send(
                embed=discord.Embed(title="Help", description=self.paginator.pages[0], color=discord.Colour.random())
            )
        else:
            ctx = self.context
            menu = SimplePages(source=EmbedSource(self.paginator.pages, 1, "Help", lambda pg: pg))
            await menu.start(ctx)


# noinspection SpellCheckingInspection
class SewentyBot(commands.Bot):
    # Lint
    owner: discord.User
    session: aiohttp.ClientSession
    pool: Optional[asyncpg.Pool]
    gspread_client: gspread_asyncio.AsyncioGspreadClientManager
    DB: motor.motor_asyncio.AsyncIOMotorDatabase  # type: ignore
    CP_DB: motor.motor_asyncio.AsyncIOMotorDatabase  # type: ignore
    LXV_DB: motor.motor_asyncio.AsyncIOMotorDatabase  # type: ignore
    GAME_COLLECTION: motor.motor_asyncio.AsyncIOMotorCollection  # type: ignore

    disabled_app_command = {"kingdom show", "kingdom upgrade", "kingdom train", "kingdom collect", "kingdom attack"}

    TOKEN = getenv("DISCORD_TOKEN")

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
            activity=discord.Game(name="s!help"),
        )
        self.gspread_client = gspread_asyncio.AsyncioGspreadClientManager(get_service_account_creds)

        self.TEST_MODE = getenv("ENV", "PRODUCTION") == "DEV"
        self.help_command = NewHelpCommand()
        self._BotBase__cogs = commands.core._CaseInsensitiveDict()  # protected member warning be like
        self.launch_timestamp = time_ns() // 1000000000

        self.banned_user = set()
        self.message_cache = MessageCache()  # Might be useful later so leaving it here

        self.afk_message = "Ded or work or college >:("

        self.TRIGGER_RESPONSE = {
            "hakid": ["<:hikablameOwO:851556784380313631>", "<:hikanoplsOwO:804522598289375232>"],
            "shifud": ["<a:BowingPandas:771010441324920853>", "<:speechlessOwO:793026526911135744>", ">.<"],
            "meo": "<a:catMIAOwO:782034693905186816>",
            "radishh": ["<a:blossomradish:812889706249453618>", "<a:radishblossom:802357456885383198>"],
            "naed": "<a:emoji3:776775391154798593>",
            "test ajg": "<:wurk:858721776770744320>",
            "xnurag": "⚠ **|** Please complete your captcha to verify that you are human! (9/6) "
            "<a:pandasmackOwO:799955371074519041>",
            "vinwuv": "osu! when",
            "invad": "When",
            "thonk": "<:PaulThink:770782702973878283>",
        }

        # we define this later
        self.guild_prefix = dict()
        self.allowed_track_channel = dict()
        self.pool = None

    async def setup_hook(self) -> None:
        if self.TEST_MODE:
            logger.warning("Test mode turned on. Consider turning off before production")
        email = getenv("EMAIL")
        password = getenv("PASSWORD")
        db_name = getenv("DB_NAME")
        cp_email = getenv("NEXT_EMAIL")
        cp_password = getenv("NEXT_PASSWORD")
        cp_name = getenv("CPDB_NAME")
        mango_url = f"mongodb+srv://{email}:{password}@{db_name}.mongodb.net/test"
        cp_url = f"mongodb+srv://{cp_email}:{cp_password}@{cp_name}.mongodb.net/Hakibot"
        psql_user = getenv("PSQL_USER")
        psql_password = getenv("PSQL_PASSWORD")
        psql_host = getenv("PSQL_HOST")
        psql_port = getenv("PSQL_PORT")
        logger.info(".env loaded")
        self.session = aiohttp.ClientSession()
        try:
            self.pool = await asyncpg.create_pool(
                host=psql_host,
                database="postgres",
                user=psql_user,
                password=psql_password,
                port=psql_port,
            )
        except Exception as e:
            logger.error(f"Error connecting psql: {e}")

        cluster = motor.motor_asyncio.AsyncIOMotorClient(mango_url, tz_aware=True)
        cluster1 = motor.motor_asyncio.AsyncIOMotorClient(cp_url, tz_aware=True)
        app = await self.application_info()
        logger.info("Aiohttp session and database connected")

        # TODO: Change to use .env
        self.owner = self.get_user(436376194166816770) or await self.fetch_user(436376194166816770)
        self.DB = cluster["Data"]
        self.CP_DB = cluster1["Hakibot"]
        self.LXV_DB = cluster1["lxv"]
        self.GAME_COLLECTION = cluster["game"]["data"]

        for file in glob(r"extensions/*.py"):
            module_name = relpath(file).replace("\\", '.').replace('/', '.')[:-3]
            await self.load_extension(module_name)
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
        if isinstance(ret, str):
            return ret
        if message.guild is not None and f"guild{message.guild.id}" in self.guild_prefix:
            ret.append(self.guild_prefix[f"guild{message.guild.id}"])
        return ret

    async def close(self) -> None:
        await self.session.close()
        await super().close()

    async def main(self) -> None:
        await self.start(self.TOKEN)  # type: ignore
    
    async def get_or_fetch_user(self, user_id: int) -> discord.User:
        user = self.get_user(user_id)
        if user is None:
            user = await self.fetch_user(user_id)
        return user
    
    async def get_or_fetch_member(self, guild: discord.Guild, member_id: int) -> discord.Member:
        member = guild.get_member(member_id)
        if member is None:
            member = await guild.fetch_member(member_id)
        return member

    async def send_owner(self, message=None, **kwargs) -> None:
        channel = await self.owner.create_dm()
        await channel.send(message, **kwargs)

    async def send_error_to_owner(
        self, error: Exception, channel: Union[discord.TextChannel, discord.Thread], command: Optional[Union[commands.Command[Any, ..., Any], str]]
    ) -> None:
        channel_name = getattr(channel, "name", "Unknown")
        output = ''.join(format_exception(type(error), error, error.__traceback__))
        if len(output) > 1500:
            buffer = BytesIO(output.encode("utf-8"))
            file = discord.File(buffer, filename="log.txt")
            await self.send_owner(
                f"Uncaught error in channel <#{channel.id}> #{channel_name} ({channel.id})\n command `{command}`",
                file=file,
            )
        else:
            custom_embed = discord.Embed(
                description=f"Uncaught error in channel <#{channel.id}> #{channel_name} ({channel.id})\n"
                f"command {command}\n"
                f"```py\n{output}\n```",
                color=discord.Colour.red(),
            )
            await self.send_owner(embed=custom_embed)

    def blocking_stack(self, traceback) -> None:
        logger.warning("Blocking code detected. You also can check from s!laststack")
        self.last_stack = traceback
        self.last_date = datetime.utcnow()

    async def get_db_ping(self) -> Optional[int]:
        if self.pool is None:
            return None
        t0 = time_ns()
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("SELECT 1")
        t1 = time_ns()
        return (t1 - t0) // 10000000


def slash_is_enabled():
    def wrapper(interaction: discord.Interaction):
        if interaction.command is None:
            return False
        return interaction.command.qualified_name not in SewentyBot.disabled_app_command

    return discord.app_commands.check(wrapper)


# TODO: Optimize read log to limit?
def read_log():
    arr = []
    with open("bot.log", encoding="utf-8") as f:
        arr = f.readlines()
    return arr


def main():
    default_banner_url = getenv("DEFAULT_BANNER_URL")

    bot = SewentyBot()

    # another dirty way to access bot var

    @bot.event
    async def on_ready():
        print(f"{bot.user.name} has connected to discord!")  # type: ignore

    @bot.tree.context_menu(name="Banner")
    async def search_banner(interaction: discord.Interaction, member: discord.Member):
        user = await bot.fetch_user(member.id)
        banner_url = user.banner or default_banner_url

        custom_embed = discord.Embed()
        custom_embed.set_author(name=f"{user.display_name}'s banner", icon_url=user.display_avatar)
        custom_embed.set_image(url=banner_url)
        await interaction.response.send_message(embed=custom_embed)

    @bot.tree.context_menu(name="Ajg", guild=discord.Object(id=714152739252338749))
    async def ajg(interaction: discord.Interaction, user: discord.User):
        await interaction.response.send_message(f"Ajg 👉 {user.mention}")

    @bot.command(hidden=True)
    @commands.is_owner()
    async def logs(ctx, page_limit=3):
        res = await bot.loop.run_in_executor(None, read_log)
        if len(res) == 0:
            return await ctx.send("No logs")
        menu = SimplePages(
            source=EmbedSource(res[-1 : -page_limit * 8 : -1], page_limit, "Logs", lambda pg: f"```.log\n{''.join(pg)}\n```")
        )
        await menu.start(ctx)

    @bot.command(hidden=True)
    @commands.is_owner()
    @commands.bot_has_guild_permissions(view_audit_log=True)
    async def alogs(ctx: commands.Context, page_limit=3, fetch_limit=3):
        if not ctx.guild:
            return

        res = [
            f"**{entry.action}:** {entry.user} -> {entry.target} (Reason: {entry.reason}) **AT:** {discord.utils.format_dt(entry.created_at)}"
            async for entry in ctx.guild.audit_logs(limit=10 * fetch_limit)
        ]

        # Normally doesn't trigger unless new guild
        if len(res) == 0:
            return await ctx.send("No logs")
        menu = SimplePages(source=EmbedSource(res, page_limit, "Logs", lambda pg: '\n'.join(pg)))
        await menu.start(ctx)

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
        # Do smth here
        await original.edit(content="Done <:wurk:858721776770744320>")

    @bot.command(hidden=True)
    @commands.is_owner()
    async def sql(ctx, *, query):
        if bot.pool is None:
            return await ctx.reply("Psql disabled", mention_author=False)
        async with bot.pool.acquire() as conn:
            async with conn.transaction():
                value = await conn.execute(query)
        await ctx.send(embed=discord.Embed(title="Result", description=value, color=discord.Colour.random()))

    @bot.command(hidden=True)
    @commands.is_owner()
    async def psql(ctx, *, query):
        if bot.pool is None:
            return await ctx.reply("Psql disabled", mention_author=False)
        async with bot.pool.acquire() as conn:
            async with conn.transaction():
                value = await conn.fetch(query)
        await ctx.send(embed=discord.Embed(title="Result", description=value, color=discord.Colour.random()))

    @psql.error
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
            custom_embed = discord.Embed(description=f"```{output}\n```", color=discord.Colour.random())
            await ctx.send(embed=custom_embed)
        elif message.stickers:
            custom_embed = discord.Embed(
                description='\n'.join(
                    [
                        f"{i}. {v.id} - {v.name}.{v.format.file_extension} " f"({v.url})"
                        for i, v in enumerate(message.stickers, start=1)
                    ]
                )
            )
            await ctx.send(embed=custom_embed)
        else:
            await ctx.send("Unable to catch fish")

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
        await ctx.reply(f"Failed to dm: `{error}`\n" f"`{type(error)}`")

    @bot.command(hidden=True)
    @commands.is_owner()
    async def switch(ctx: commands.Context, command: bot.get_command):  # type: ignore
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
        await ctx.reply(f"Failed to send: `{error}`\n" f"`{type(error)}`")

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
        channel_id = str(channel_id)  # type: ignore
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
        t = await bot.get_db_ping()
        custom_embed = discord.Embed(
            title="Bot Stats",
            description=f"Uptime: <t:{bot.launch_timestamp}:R>\n"
            f"Total Servers: {count_guild}\n"
            f"Bot Ver: {__version__}\n"
            f"CPU usage: {psutil.cpu_percent(1)}%\n"
            f"Ping: "
            f"{round(bot.latency * 1000)} ms\n"
            f"DB Ping: {t} ms\n"
            f"Running in **"
            f"{'Production' if not bot.TEST_MODE else 'Dev'}** mode ",
            color=discord.Colour.random(),
        )
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
            return await channel.send(embed=dm_embed)  # type: ignore

        if bot.TEST_MODE:
            return await bot.process_commands(message)

        if "inva" in message.content.lower():
            await bot.send_owner(
                f"Mentioned 'inva' at {message.channel.mention} #{message.channel.name} **Guild** {message.guild.name}\n"  # type: ignore
                f"**By:** {message.author} ({message.author.id})\n"
                f"**Jump:** {message.jump_url}\n"
                f"**Full:**\n"
                f"{message.content}"
            )

        guild_id = message.guild.id
        if guild_id == 714152739252338749:
            low_msg = message.content.lower()

            for u in message.mentions:
                if not isinstance(u, discord.Member):
                    continue
                if (
                    u.id == bot.owner.id
                    and (
                        u.status == discord.Status.idle
                        or u.status == discord.Status.dnd
                        or u.status == discord.Status.offline
                    )
                    and bot.afk_message is not None
                ):
                    await message.reply(
                        f"<a:running:791350508375900190> **Owner AFK:** {bot.afk_message}",
                        mention_author=False,
                        allowed_mentions=discord.AllowedMentions.none(),
                    )

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
    async def on_message_edit(before: discord.Message, after: discord.Message):
        if bot.TEST_MODE:
            return
        if before.author.id == 571027211407196161 and str(before.channel.id) in bot.allowed_track_channel:
            catch_ = after.embeds
            if not catch_:
                return
            processed = catch_[-1]
            prev_catch_ = before.embeds
            try:
                message = processed.fields[0].value
                if message is None:
                    return
                if (
                    prev_catch_
                    and prev_catch_[-1].fields is not None
                    and prev_catch_[-1].fields[0].value is not None
                    and prev_catch_[-1].fields[0].value == message  # Better compare alg?
                ):  # Compare with previous edited message
                    return
            except (KeyError, IndexError):
                return
            """
            Line 1: **[Round X]**
            Line 2: Prev action
            Line 3: Latest action
            """
            arr = message.split('\n')
            if len(arr) < 3:
                return
            latest = arr[2]  # Abuse dynamic type
            if (
                (
                    "CRITICAL HIT" in latest
                    and (bot.allowed_track_channel[str(after.channel.id)] or "Rage Mode" not in message)
                )
                or "managed to evade" in latest
                or "fortunately it resisted" in latest
                or "uses **Lucky Coin**" in latest
                or "uses **Unlucky Coin**" in latest
                or "blinded by the smoke" in latest
            ):
                message = message.replace("<:ARROW:698301107419611186>", ":arrow_right: ")
                custom_embed = discord.Embed(
                    title=arr[0].split('[')[1].split(']')[0],
                    description=arr[1] + '\n' + latest,
                    color=discord.Colour.blue(),
                )
                custom_embed.set_footer(
                    text="psst. If you want this tracker, DM/tell invaliduser77 (Tracker is fixed. If there's bug, please report immediately)"
                )
                await after.channel.send(embed=custom_embed)

    @bot.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        if isinstance(error, discord.app_commands.errors.CommandNotFound):
            return
        if isinstance(error, discord.app_commands.errors.CheckFailure):
            return await interaction.response.send_message("You can't use this command or command on maintenance")
        output = ''.join(format_exception(type(error), error, error.__traceback__))
        if interaction.channel is None:
            return
        if len(output) > 1500:
            buffer = BytesIO(output.encode("utf-8"))
            file = discord.File(buffer, filename="log.txt")
            await bot.send_owner(
                f"Uncaught error in channel <#{interaction.channel.id}> " f"command `{interaction.command}`", file=file
            )
        else:
            custom_embed = discord.Embed(
                description=f"Uncaught error in channel <#{interaction.channel.id}> "
                f"command {interaction.command}\n"
                f"```py\n{output}\n```",
                color=discord.Colour.red(),
            )
            await bot.send_owner(embed=custom_embed)

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.errors.CommandNotFound) or hasattr(ctx.command, "on_error"):
            return
        if isinstance(error, commands.errors.DisabledCommand):
            return await ctx.reply(
                "This command is disabled or under maintenance <:speechlessOwO:793026526911135744>", mention_author=False
            )
        if isinstance(error, commands.errors.CheckFailure):
            return await ctx.reply("You are not allowed to use this command", mention_author=False)
        if isinstance(error, commands.errors.CommandOnCooldown):
            return await ctx.reply(
                f"{error} <:angeryV2:810860324248616960>", mention_author=False, delete_after=error.retry_after
            )
        if (
            isinstance(error, commands.errors.NotOwner)
            or isinstance(error, discord.errors.Forbidden)
            or isinstance(error, commands.errors.BadArgument)
            or isinstance(error, commands.errors.MissingRequiredArgument)
        ):
            return await ctx.reply(error, mention_author=False)
        if isinstance(error, commands.errors.UserNotFound):
            return await ctx.reply("User not found", mention_author=False)
        await bot.send_error_to_owner(error, ctx.channel, ctx.command)

    asyncio.run(bot.main())


if __name__ == '__main__':
    main()
