from __future__ import annotations

import logging

import discord
from discord.ext import commands
import googletrans
# import wikipedia

import asyncio
import base64
import datetime
from math import ceil, log
import os
import random
from typing import TYPE_CHECKING, Optional, Union, List, Annotated

from constants import USER_AGENTS
from utils.view_util import Dropdown

if TYPE_CHECKING:
    from main import SewentyBot

logger = logging.getLogger(__name__)


def is_win(player_pos, current_player):
    combination = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [1, 4, 7], [2, 5, 8], [3, 6, 9], [1, 5, 9], [3, 5, 7]]
    for x in combination:
        if all(y in player_pos[current_player] for y in x):
            return True
    return False


def is_draw(player_pos):
    if len(player_pos[":one:"]) + len(player_pos[":two:"]) == 9:
        return True
    return False


def render_spotify_embed(member: discord.Member, spotify: Optional[discord.Spotify] = None) -> Union[str, discord.Embed]:  # type: ignore
    # In most cases the filtered list consist only 1 element unless there are breaking changes
    spotify: discord.Spotify
    spotify = spotify or list(filter(lambda a: isinstance(a, discord.Spotify), member.activities))  # type: ignore
    if not spotify:
        return "Not listening ):<"
    if isinstance(spotify, list):
        spotify = spotify[-1]
    # if there are more than 1 artists, put them all
    duration = int(spotify.end.timestamp() - spotify.start.timestamp())
    ongoing = int(datetime.datetime.now(datetime.timezone.utc).timestamp() - spotify.start.timestamp())
    percentage = round(ongoing / duration * 100)
    emoji = f"{'<:start0:969180226208813066>' if percentage >= 10 else '<:start1:969180368852910120>'}" \
            f"{'<:middle0:969180275525443636>' * (0 if percentage <= 10 else min(ceil(percentage / 10) - 1, 8))}" \
            f"{'<:middle1:969180413845188619>' * (8 if percentage <= 10 else max(9 - ceil(percentage / 10), 0))}" \
            f"{'<:end0:969180313525821470>' if percentage > 90 else '<:end1:969180520695103508>'}"
    artist = spotify.artist if len(spotify.artists) > 1 else ', '.join(spotify.artists)
    custom_embed = discord.Embed(title=f"{member.name} is listening to a song",
                                 description=f"Title: [{spotify.title}]({spotify.track_url})\n"
                                             f"Artist: {artist}\n"
                                             f"Album: {spotify.album}\n"
                                             f"{emoji}", color=spotify.color)
    custom_embed.set_thumbnail(url=spotify.album_cover_url)
    return custom_embed


class ActivityView(discord.ui.View):
    def __init__(self, user: discord.User, target: discord.Member):
        super().__init__()
        self.user = user
        self.target = target


class ActivityDropdown(Dropdown):
    def __init__(self, text: str, select_list: List[discord.SelectOption]):

        super().__init__(text, select_list)
        self.activities = {}

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: ActivityView = self.view
        if interaction.user.id != view.user.id:
            return await interaction.response.send_message("You are not allowed to do this :c", ephemeral=True)

        if self.values[0] == "Spotify":
            try_embed = render_spotify_embed(view.target, self.activities["Spotify"])
            if isinstance(try_embed, str):
                return await interaction.response.send_message("User ended listening session", ephemeral=True)
            return await interaction.response.edit_message(embed=try_embed, view=None)

        activity: discord.Activity = self.activities[self.values[0]]
        custom_embed = discord.Embed(color=discord.Colour.random())
        custom_embed.set_author(name=str(view.target), icon_url=view.target.display_avatar)

        start = activity.start
        if start is None:
            start = -1e+13
        else:
            start = start.timestamp()

        if activity.large_image_url:
            custom_embed.set_thumbnail(url=activity.large_image_url)
        custom_embed.add_field(name="Details",
                               value=f"{activity.details or 'No details :c'}\n"
                                     f"Name: {activity.name}\n"
                                     f"State: {activity.state}\n"
                                     f"Type: {activity.type.name}\n"
                                     f"Started at: <t:{int(start)}:D>\n"
                                     f"Large image text: {activity.large_image_text}\n"
                                     f"Small image text: {activity.small_image_text}")
        if activity.application_id:
            custom_embed.set_footer(text=f"Application id: {activity.application_id}")
        await interaction.response.edit_message(embed=custom_embed, view=None)


class Language(commands.FlagConverter, delimiter=' ', prefix='--'):
    lang: str


# noinspection SpellCheckingInspection
class Miscellaneous(commands.Cog):
    def __init__(self, bot: SewentyBot):
        self.bot: SewentyBot = bot
        self.translator = googletrans.Translator()
        self.occupied_channel = set()
        self.current_token = tuple()
        self.current_spotify_token = tuple()

        self.CLIENT_ID = os.getenv("CLIENT_ID")
        self.CLIENT_SECRET = os.getenv("CLIENT_SECRET")
        self.SPOTIFY_ID = os.getenv("SPOTIFY_ID")
        self.SPOTIFY_SECRET = os.getenv("SPOTIFY_SECRET")
        self.OSU_API_URL = "https://osu.ppy.sh/api/v2"
        self.OSU_TOKEN_URL = "https://osu.ppy.sh/oauth/token"
        self.SPOTIFY_API_URL = "https://api.spotify.com/v1"
        self.SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
        
    @property
    def magic_header(self):
        return {
            "User-Agent": random.choice(USER_AGENTS)
        }

    # TODO: Wikipedia command?
    @commands.command(name="wikipedia", enabled=False)
    @commands.cooldown(rate=1, per=10.0, type=commands.BucketType.user)
    async def check_wiki(self, ctx):
        """
        Still in Work
        """
        pass

    @commands.command(name="flipcoin", aliases=['coinflip', 'cf'])
    async def flip_coin(self, ctx):
        """
        Flips a coin
        """

        coin_face = random.choice(["Head", "Tail"])
        await ctx.send(f'**{coin_face}** of the coin')

    @commands.command()
    async def rps(self, ctx, choice: Optional[str] = None):
        """
        Rock paper scissor
        """
        rps_list = ['ROCK', 'PAPER', 'SCISSOR']
        rpsgame = random.choice(rps_list)
        if choice:
            choice = choice.upper()
        if not choice:
            await ctx.send(f'||{rpsgame}||')
        elif choice in rps_list:
            result = ''
            if choice == rpsgame:
                result = 'Draw'
            elif choice == 'ROCK':
                if rpsgame == 'SCISSOR':
                    result = 'Win'
                else:
                    result = 'Lose'
            elif choice == 'PAPER':
                if rpsgame == 'ROCK':
                    result = 'Win'
                else:
                    result = 'Lose'
            elif choice == 'SCISSOR':
                if rpsgame == 'PAPER':
                    result = 'Win'
                else:
                    result = 'Lose'
            await ctx.send(f'You {result}! you choose {choice}, I choose {rpsgame}')
        else:
            await ctx.send(f"Please input correct argument. You should choose rock, paper or scissor")

    @commands.command(name="type", help="You wonder why this command exist")
    async def typing(self, ctx: commands.Context):
        async with ctx.typing():
            pass

    @commands.command(name="tictactoe", help="Yes it is")
    async def tic_game(self, ctx, opponent: discord.User):
        if opponent == ctx.author:
            await ctx.send("Do you need friend?", delete_after=5)
            return
        if ctx.channel.id in self.occupied_channel:
            return

        await ctx.send(f'{opponent.mention} Do you want to accept?')

        def accepted_battle(m):
            if m.channel.id != ctx.channel.id:
                return False
            if m.content.lower() in ["yes", "y"] and m.author.id == opponent.id:
                return True
            elif m.content.lower() in ["no", "n"] and m.author.id == opponent.id:
                raise asyncio.TimeoutError
            return False

        try:
            await self.bot.wait_for("message", check=accepted_battle, timeout=15.0)
        except asyncio.TimeoutError:
            await ctx.send("Opponent did not accept")
            return

        selected_player = ctx.author
        cursor = ":one:"
        board = ["🟦" for _ in range(9)]
        player_pos = {":one:": [], ":two:": []}
        winner = ""
        done = False
        self.occupied_channel.add(ctx.channel.id)

        def valid_position(m):
            if m.channel.id != ctx.channel.id:
                return False
            if not m.content.isdigit() or not m.author == selected_player:
                return False
            if int(m.content) < 1 or int(m.content) > 9:
                return False
            return True

        while not done:
            choice = False
            content = f"{board[0]} {board[1]} {board[2]}\n" \
                      f"{board[3]} {board[4]} {board[5]}\n" \
                      f"{board[6]} {board[7]} {board[8]}"
            custom_embed = discord.Embed(title=f'{selected_player} to go',
                                         description=content)
            custom_embed.set_footer(text="Select position from 1 - 9")
            await ctx.send(embed=custom_embed)
            try:
                while not choice:
                    choice = await self.bot.wait_for("message", check=valid_position, timeout=60.0)
                    if board[int(choice.content) - 1] != "🟦":
                        await ctx.send("Place already occupied", delete_after=3)
                        choice = False
            except asyncio.TimeoutError:
                if selected_player == opponent:
                    winner = ctx.author
                else:
                    winner = opponent
                await ctx.send(f"{selected_player} did not answer in 1 minute")
                done = True
                continue
            board[int(choice.content) - 1] = cursor
            player_pos[cursor].append(int(choice.content))

            if is_win(player_pos, cursor):
                winner = selected_player
                done = True
                continue
            if is_draw(player_pos):
                winner = "DRAW"
                done = True
                continue

            if selected_player == ctx.author:
                selected_player = opponent
                cursor = ":two:"
            else:
                selected_player = ctx.author
                cursor = ":one:"

        self.occupied_channel.remove(ctx.author.channel)
        if winner == "DRAW":
            await ctx.send("Game drawn")
            return
        content = f"{board[0]} {board[1]} {board[2]}\n" \
                  f"{board[3]} {board[4]} {board[5]}\n" \
                  f"{board[6]} {board[7]} {board[8]}"
        custom_embed = discord.Embed(title='Final Board',
                                     description=content)
        custom_embed.add_field(name="Result", value=f"{winner} Won")
        await ctx.send(embed=custom_embed)

    @commands.command(name="guessnumber", help="Guess when")
    async def guessing(self, ctx, difficulty: int = 1, max_attempt: Optional[int] = None):
        if ctx.channel.id in self.occupied_channel:
            return
        if difficulty < 1:
            return await ctx.reply("Are you scared to guess? Pick difficulty from 1 to 3", mention_author=False)
        if difficulty > 3:
            return await ctx.reply("Too big! Pick dificulty from 1 to 3", mention_author=False)
        multiplier = 100 ** difficulty
        min_number = random.randrange(1, 101, 10)
        max_number = min_number * multiplier
        if not max_attempt:
            max_attempt = ceil(log(max_number - min_number + 2, 2)) + 1
        selected_number = random.randrange(min_number, max_number + 1)
        await ctx.send(f"Guess number from {min_number} - {max_number}")
        attempt = 0

        def valid_number(m):
            if m.channel.id != ctx.channel.id:
                return False
            if not m.content.isdigit():
                return False
            if int(m.content) < min_number or int(m.content) > max_number:
                return False
            return True

        self.occupied_channel.add(ctx.channel.id)
        while attempt <= max_attempt:
            try:
                guess = await self.bot.wait_for("message", check=valid_number, timeout=60)
            except asyncio.TimeoutError:
                await ctx.send("You don't guess in 1 minute. aborting")
                self.occupied_channel.remove(ctx.channel.id)
                return
            if int(guess.content) < selected_number:
                await ctx.send(f"**Low**, {max_attempt - attempt} left\n"
                               f"Range: {min_number} - {max_number}")
            elif int(guess.content) > selected_number:
                await ctx.send(f"**High**, {max_attempt - attempt} left\n"
                               f"Range: {min_number} - {max_number}")
            else:
                await ctx.send(f"Correct. Guessed in {attempt} attempt")
                self.occupied_channel.remove(ctx.channel.id)
                return
            attempt += 1
        self.occupied_channel.remove(ctx.channel.id)
        await ctx.send(f"You failed to guess. Correct: {selected_number}")

    async def get_token(self, token_url):
        current = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        last_token, expired = self.current_token or (None, None)
        # this logic looks dirty
        if last_token is not None and expired is not None and current + 100 < expired:
            return last_token
        data = {
            "client_id": int(self.CLIENT_ID),  # type: ignore
            "client_secret": self.CLIENT_SECRET,
            "grant_type": "client_credentials",
            "scope": "public"
        }
        async with self.bot.session.post(token_url, data=data) as response:
            res = await response.json()
        self.current_token = (res["access_token"], current + res["expires_in"])
        return res["access_token"]
    
    async def get_spotify_token(self, token_url):
        """
        Basically get osu token but spotify
        """
        current = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        last_token, expired = self.current_spotify_token or (None, None)
        if last_token is not None and expired is not None and current + 100 < expired:
            return last_token
        auth_header = base64.urlsafe_b64encode(f"{self.SPOTIFY_ID}:{self.SPOTIFY_SECRET}".encode())
        headers = {
            "Authorization": f"Basic {auth_header.decode()}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        params = {
            "grant_type": "client_credentials"
        }
        async with self.bot.session.post(token_url, params=params, headers=headers) as response:
            res = await response.json()

        self.current_spotify_token = (res["access_token"], current + res["expires_in"])
        return res["access_token"]

    @commands.command(name="osutop", help="Flex your top osu play")
    @commands.cooldown(rate=1, per=15.0, type=commands.BucketType.user)
    async def get_osu_top(self, ctx, username, limit: int = 5):
        if limit > 10:
            return await ctx.reply("Too big :c", mention_author=False)

        message = await ctx.send("Connecting <a:discordloading:792012369168957450>")

        token = await self.get_token(self.OSU_TOKEN_URL)
        headers = {
            "Content_Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
        params = {
            "mode": "osu",
            "limit": limit
        }
        async with self.bot.session.get(f"{self.OSU_API_URL}/users/{username}",
                                        params=params,
                                        headers=headers) as response1:

            if response1.status != 200:
                return await message.edit(content=f"Failed to find user. Error code {response1.status}")

            find_username = await response1.json()
            userid = find_username["id"]

            async with self.bot.session.get(f"{self.OSU_API_URL}/users/{userid}/scores/best",
                                            params=params,
                                            headers=headers) as response2:

                if response2.status != 200:
                    return await message.edit(content=f"Failed to get score. Error code {response2.status}")

                raw = await response2.json()

        if len(raw) < 1:
            return await message.edit(content="No scores to show")

        custom_embed = discord.Embed(title=find_username["username"],
                                     description=f"Top {limit} map",
                                     color=discord.Colour.random())
        custom_embed.set_thumbnail(url=find_username["avatar_url"])
        for entry in raw:
            title = entry["beatmapset"]["title"]
            title_url = entry["beatmap"]["url"]
            statistic = entry["statistics"]
            count_50, count_100, count_300 = statistic["count_50"], statistic["count_100"], statistic["count_300"]
            count_geki, count_katu = statistic["count_geki"], statistic["count_katu"]
            count_miss = statistic["count_miss"]
            pp = entry["pp"]
            difficulty_ver = entry["beatmap"]["version"]
            difficulty_rating = entry["beatmap"]["difficulty_rating"]
            accuracy = entry["accuracy"]
            max_combo = entry["max_combo"]
            rank = entry["rank"].replace('H', " Hidden")
            mods = " ".join(entry["mods"])
            custom_embed.add_field(name=f"{title} ⭐ {difficulty_rating}",
                                   value=f"[{difficulty_ver}]({title_url})\n"
                                         f"PP: {pp} | {round(accuracy * 100, 1)}% | {max_combo}x **[{rank}]**\n"
                                         f"Mod(s): {mods}\n"
                                         f"**300**: {count_300} | **100**: {count_100} | **50**: {count_50}\n"
                                         f"**激**: {count_geki} | **喝**: {count_katu} | **X**: {count_miss}",
                                   inline=False)
        await ctx.send(embed=custom_embed)
        await message.delete()

    @commands.command(name="osurecent", help="Show your recent osu play")
    @commands.cooldown(rate=1, per=15.0, type=commands.BucketType.user)
    async def get_osu_recent(self, ctx, username, limit: int = 5):
        if limit > 10:
            return await ctx.reply("Too big :c", mention_author=False)

        message = await ctx.send("Connecting <a:discordloading:792012369168957450>")

        token = await self.get_token(self.OSU_TOKEN_URL)
        headers = {
            "Content_Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
        params = {
            "mode": "osu",
            "limit": limit,
        }
        async with self.bot.session.get(f"{self.OSU_API_URL}/users/{username}",
                                        params=params,
                                        headers=headers) as response1:

            if response1.status != 200:
                return await message.edit(content=f"Failed to find user. Error code {response1.status}")

            find_username = await response1.json()
            userid = find_username["id"]

            async with self.bot.session.get(f"{self.OSU_API_URL}/users/{userid}/scores/recent",
                                            params=params,
                                            headers=headers) as response2:

                if response2.status != 200:
                    return await message.edit(content=f"Failed to get score. Error code {response2.status}")

                raw = await response2.json()

        if len(raw) < 1:
            return await message.edit(content="No scores to show")

        custom_embed = discord.Embed(title=find_username["username"],
                                     description=f"Top {limit} map",
                                     color=discord.Colour.random())
        custom_embed.set_thumbnail(url=find_username["avatar_url"])
        for entry in raw:
            title = entry["beatmapset"]["title"]
            title_url = entry["beatmap"]["url"]
            statistic = entry["statistics"]
            count_50, count_100, count_300 = statistic["count_50"], statistic["count_100"], statistic["count_300"]
            count_geki, count_katu = statistic["count_geki"], statistic["count_katu"]
            count_miss = statistic["count_miss"]
            pp = entry["pp"]
            difficulty_ver = entry["beatmap"]["version"]
            difficulty_rating = entry["beatmap"]["difficulty_rating"]
            accuracy = entry["accuracy"]
            max_combo = entry["max_combo"]
            rank = entry["rank"].replace('H', " Hidden")
            mods = " ".join(entry["mods"])
            custom_embed.add_field(name=f"{title} ⭐ {difficulty_rating}",
                                   value=f"[{difficulty_ver}]({title_url})\n"
                                         f"PP: {pp} | {round(accuracy * 100, 1)}% | {max_combo}x **[{rank}]**\n"
                                         f"Mod(s): {mods}\n"
                                         f"**300**: {count_300} | **100**: {count_100} | **50**: {count_50}\n"
                                         f"**激**: {count_geki} | **喝**: {count_katu} | **X**: {count_miss}",
                                   inline=False)
        await message.edit(content=None, embed=custom_embed)

    @commands.command(name="osulast", help="Last play of your osu")
    @commands.cooldown(rate=1, per=15.0, type=commands.BucketType.user)
    async def get_last_osu_play(self, ctx, username):
        message = await ctx.send("Connecting <a:discordloading:792012369168957450>")

        token = await self.get_token(self.OSU_TOKEN_URL)
        headers = {
            "Content_Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
        params = {
            "mode": "osu",
            "limit": 1,
            "include_fails": 1
        }
        async with self.bot.session.get(f"{self.OSU_API_URL}/users/{username}",
                                        params=params,
                                        headers=headers) as response1:

            if response1.status != 200:
                return await message.edit(content=f"Failed to find user. Error code {response1.status}")

            find_username = await response1.json()
            userid = find_username["id"]

            async with self.bot.session.get(f"{self.OSU_API_URL}/users/{userid}/scores/recent",
                                            params=params,
                                            headers=headers) as response2:

                if response2.status != 200:
                    return await message.edit(content=f"Failed to get score. Error code {response2.status}")

                raw = await response2.json()

        if len(raw) < 1:
            return await message.edit(content="No scores to show")

        raw = raw[0]
        custom_embed = discord.Embed(color=discord.Colour.random())
        custom_embed.set_author(name=find_username["username"],
                                icon_url=find_username["avatar_url"])
        title = raw["beatmapset"]["title"]
        title_url = raw["beatmap"]["url"]
        statistic = raw["statistics"]
        count_50, count_100, count_300 = statistic["count_50"], statistic["count_100"], statistic["count_300"]
        count_geki, count_katu = statistic["count_geki"], statistic["count_katu"]
        count_miss = statistic["count_miss"]
        pp = raw["pp"]
        difficulty_ver = raw["beatmap"]["version"]
        difficulty_rating = raw["beatmap"]["difficulty_rating"]
        accuracy = raw["accuracy"]
        max_combo = raw["max_combo"]
        rank = raw["rank"].replace('H', " Hidden")
        mods = " ".join(raw["mods"])
        custom_embed.add_field(name=f"{title} ⭐ {difficulty_rating}",
                               value=f"[{difficulty_ver}]({title_url})\n"
                                     f"PP: {pp} | {round(accuracy * 100, 1)}% | {max_combo}x **[{rank}]**\n"
                                     f"Mod(s): {mods}\n"
                                     f"**300**: {count_300} | **100**: {count_100} | **50**: {count_50}\n"
                                     f"**激**: {count_geki} | **喝**: {count_katu} | **X**: {count_miss}",
                               inline=False)
        beatmap = raw["beatmap"]
        custom_embed.add_field(name="Map details",
                               value=f"**{beatmap['bpm']} BPM**\n"
                                     f"AR **{beatmap['ar']}** | CS **{beatmap['cs']}**\n"
                                     f"HP **{beatmap['drain']}** | OD **{beatmap['accuracy']}**\n"
                                     f"Circles count: {beatmap['count_circles']}\n"
                                     f"Slider count: {beatmap['count_sliders']}\n"
                                     f"Spinner count: {beatmap['count_spinners']}")
        custom_embed.set_thumbnail(url=raw["beatmapset"]["covers"]["cover"])
        # async with self.bot.session.get("https://" + raw["beatmapset"]["preview_url"][2:]) as response:
        #     if response.status == 200:
        #         preview = io.BytesIO(await response.read())
        #         await message.delete()
        #         return await ctx.send(file=discord.File(preview, "preview.mp3"), embed=custom_embed)
        await message.edit(content=None, embed=custom_embed)

    @commands.command(name="osuprofile", help="Flex your osu profile")
    @commands.cooldown(rate=1, per=15.0, type=commands.BucketType.user)
    async def get_osu_profile(self, ctx, username):
        message = await ctx.send("Connecting <a:discordloading:792012369168957450>")

        token = await self.get_token(self.OSU_TOKEN_URL)
        headers = {
            "Content_Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
        params = {
            "mode": "osu",
        }
        async with self.bot.session.get(f"{self.OSU_API_URL}/users/{username}",
                                        params=params,
                                        headers=headers) as response:
            if response.status != 200:
                return await ctx.send(content=f"Failed to get user. Error code: {response.status}")
            raw = await response.json()
        custom_embed = discord.Embed()
        custom_embed.set_author(name=raw["username"])
        custom_embed.set_thumbnail(url=raw["avatar_url"])
        statistic = raw["statistics"]
        string = ""
        for i in statistic:
            if isinstance(statistic[i], dict):
                for j in statistic[i]:
                    name = j.replace("_", " ")
                    name = name.capitalize() if len(name) > 3 else name.upper()
                    string += f"{name}: {statistic[i][j]}\n"
                continue
            name = i.replace('_', ' ')
            name = name.capitalize() if len(name) > 3 else name.upper()
            string += f"{name}: {statistic[i]}\n"
        custom_embed.add_field(name="Details", value=string)
        custom_embed.add_field(name="Other", value=f"Online: {raw['is_online']}\n"
                                                   f"Active: {raw['is_active']}\n"
                                                   f"Discord: {raw['discord']}")
        custom_embed.set_footer(text=f"Joined at {raw['join_date']}")
        await message.edit(content=None, embed=custom_embed)

    @commands.command(name="spotify", aliases=["spot", "spt"])
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def activity_spotify(self, ctx, member: Optional[discord.Member] = None):
        if not member:
            member = ctx.author

        try_embed = render_spotify_embed(member)  # type: ignore
        if isinstance(try_embed, str):
            return await ctx.send(try_embed)
        await ctx.send(embed=try_embed)

    @commands.command(aliases=["a", "act"])
    async def activity(self, ctx, member: Optional[discord.Member] = None):  # type: ignore
        member: discord.Member
        if not member:
            member = ctx.author
        filtered_activities = list(filter(lambda x: not isinstance(x, discord.CustomActivity), member.activities)) 
        if len(filtered_activities) < 1:
            return await ctx.send("No activities")
        dropdown = ActivityDropdown(text="Select activities",
                                    select_list=[
                                        discord.SelectOption(label=a.name) for a in filtered_activities  # type: ignore
                                    ])
        dropdown.activities = {a.name: a for a in filtered_activities}
        view = ActivityView(ctx.author, member)
        view.add_item(dropdown)
        await ctx.send(view=view)

    @commands.command(name="spotifysong", aliases=["spts"])
    @commands.cooldown(rate=1, per=15.0, type=commands.BucketType.user)
    async def spotify_song(self, ctx, *, name):
        """
        Search for spotify track
        """

        message = await ctx.send("Connecting <a:discordloading:792012369168957450>")
        token = await self.get_spotify_token(self.SPOTIFY_TOKEN_URL)
        headers = {
            "Content_Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
        params = {
            'q': name,
            "type": "track",
            "limit": 3
        }
        async with self.bot.session.get(f"{self.SPOTIFY_API_URL}/search",
                                        params=params,
                                        headers=headers) as response:
            if response.status != 200:
                return await ctx.send(content=f"Failed to get user. Error code: {response.status}")
            raw = await response.json()
        custom_embed = discord.Embed(title="Result", color=discord.Colour.random())
        custom_embed.set_thumbnail(url=raw["tracks"]["items"][0]["album"]["images"][0]["url"])
        custom_embed.set_footer(text="Want more search result? subscribe to onlyfans")
        for item in raw["tracks"]["items"]:
            duration_ms = item["duration_ms"]
            custom_embed.add_field(name=item["name"],
                                   value=f"[URL]({item['external_urls']['spotify']})\n"
                                         f"Artist: {', '.join([a['name'] for a in item['artists']])}\n"
                                         f"Duration: {duration_ms//60000} m {(duration_ms // 1000) % 60} s\n"
                                         f"Popularity: {item['popularity']}",
                                   inline=False)
        await message.edit(content=None, embed=custom_embed)

    @commands.command(name="spotifyartist", aliases=["spta"])
    @commands.cooldown(rate=1, per=15.0, type=commands.BucketType.user)
    async def spotify_artist(self, ctx, *, name):
        """
        Search for spotify artist
        """
        message = await ctx.send("Connecting <a:discordloading:792012369168957450>")
        token = await self.get_spotify_token(self.SPOTIFY_TOKEN_URL)
        headers = {
            "Content_Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
        params = {
            'q': name,
            "type": "artist",
            "limit": 3
        }
        async with self.bot.session.get(f"{self.SPOTIFY_API_URL}/search",
                                        params=params,
                                        headers=headers) as response:
            if response.status != 200:
                return await ctx.send(content=f"Failed to get user. Error code: {response.status}")
            raw = await response.json()

        custom_embed = discord.Embed(title="Result", color=discord.Colour.random())
        custom_embed.set_thumbnail(url=raw["artists"]["items"][0]["images"][0]["url"])
        custom_embed.set_footer(text="Want more search result? subscribe to onlyfans")

        for item in raw["artists"]["items"]:
            custom_embed.add_field(name=item["name"],
                                   value=f"[URL]({item['external_urls']['spotify']})\n"
                                         f"Genres: {', '.join(item['genres'])}\n"
                                         f"Followers: {item['followers']['total']}",
                                   inline=False)
        await message.edit(content=None, embed=custom_embed)

    @commands.command(aliases=["tl"])
    @commands.cooldown(rate=1, per=20.0, type=commands.BucketType.user)
    async def translate(self, ctx: commands.Context, *, text: Annotated[Optional[str], commands.clean_content] = None):
        """
        Translate accrucy 99% same as Google Translate with cost of high risk being blocked :c
        Use it wisely
        Put language code at last to translate other language
        Examples s!tl text -id
        """
        last = text.split(' ')[-1] if text is not None else ''
        if text is None or (len(text.split(' ')) < 2 and last.startswith('-')):
            ref = ctx.message.reference
            if ref is not None and isinstance(ref.resolved, discord.Message):
                text = ref.resolved.content
            else:
                return await ctx.reply("Where text :c", mention_author=False)
        lang = "en"
        if last.startswith('-') and last.removeprefix('-') in googletrans.LANGUAGES:
            lang = last.removeprefix('-')
            text = text.removesuffix(last)
        if len(text) > 1000:
            return await ctx.reply("Too long :c", mention_author=False)

        # res = await self.bot.loop.run_in_executor(None, self.translator.translate, text)
        # custom_embed = discord.Embed(color=discord.Colour.random())
        # src = googletrans.LANGUAGES.get(res.src, "auto detect").title()
        # dest = googletrans.LANGUAGES.get(res.dest, "auto detect").title()
        # custom_embed.add_field(name=f"Original ({src})", value=res.origin, inline=False)
        # custom_embed.add_field(name=f"Translated ({dest})", value=res.text, inline=False)

        # https://github.com/Animenosekai/translate/blob/main/translatepy/translators/google.py#L322-L375
        params = {
            "client": "gtx",
            "dj": 1,
            "dt": 't',
            'q': text,
            "sl": "auto",
            "tl": lang}
        link = "https://clients5.google.com/translate_a/single?"
        async with self.bot.session.get(link, params=params, headers=self.magic_header) as r:
            if r.status != 200:
                return await ctx.reply(f"Error status {r.status}", mention_author=False)
            data = await r.json()
        custom_embed = discord.Embed(color=discord.Colour.random())
        src = googletrans.LANGUAGES.get(data["src"], "auto detect").title()
        lang_format = '\n'.join(f"**{googletrans.LANGUAGES.get(lang, 'unknown').title()}** "
                                f"({round(confidence * 100, 1)}%)" for lang, confidence in
                                zip(data["ld_result"]["srclangs"], data["ld_result"]["srclangs_confidences"]))
        custom_embed.add_field(name=f"Original ({src} {round(data['confidence'] * 100, 1)}%)",
                               value=''.join(section["orig"] for section in data["sentences"]), inline=False)
        custom_embed.add_field(name=f"Translated {googletrans.LANGUAGES.get(lang, 'Unknown')}",
                               value=''.join(section["trans"] for section in data["sentences"]), inline=False)
        custom_embed.add_field(name="Detected language",
                               value=lang_format, inline=False)
        await ctx.send(embed=custom_embed)


async def setup(bot: SewentyBot):
    await bot.add_cog(Miscellaneous(bot))
