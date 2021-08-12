import discord
from discord.ext import commands
import wikipedia
import random
import asyncio
import os
from math import ceil, log
import aiohttp
occupied_channel = set()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")


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


class Miscellaneous(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='wikipedia', help='Ah yes wikipedia')
    async def checkwiki(self, ctx, key, option, number: int = None, lang=None):
        if key and option and number:
            if lang:
                wikipedia.set_lang(lang)
            if option == '-sc':
                resu = wikipedia.search(key, results=number)
                result = ', '.join(resu)
            elif option == '-su':
                result = wikipedia.summary(key, sentences=number)
            else:
                await ctx.send("Please input option", delete_after=5)
                return
            if number > 30:
                await ctx.send("Too long :c")
                return
        else:
            await ctx.send('Please input complete argument. Ex: wikipedia -su 5', delete_after=8)
            return
        custom_embed = discord.Embed(title=key, description=result)
        wikipedia.set_lang('en')
        await ctx.send(embed=custom_embed)

    @commands.command(name='flipcoin', help='Flip coin', aliases=['coinflip', 'cf'])
    async def flip_coin(self, ctx):
        coinface = random.choice(["Head", "Tail"])
        await ctx.send(f'**{coinface}** of the coin')

    @commands.command(name='rps', help='Rock paper scissor')
    async def ropasci(self, ctx, rpschoice: str = None):
        rpclist = ['ROCK', 'PAPER', 'SCISSOR']
        rpsgame = random.choice(rpclist)
        if rpschoice:
            rpschoice = rpschoice.upper()
        if not rpschoice:
            await ctx.send(f'||{rpsgame}||')
        elif rpschoice in rpclist:
            result = ''
            if rpschoice == rpsgame:
                result = 'Draw'
            elif rpschoice == 'ROCK':
                if rpsgame == 'SCISSOR':
                    result = 'Win'
                else:
                    result = 'Lose'
            elif rpschoice == 'PAPER':
                if rpsgame == 'ROCK':
                    result = 'Win'
                else:
                    result = 'Lose'
            elif rpschoice == 'SCISSOR':
                if rpsgame == 'PAPER':
                    result = 'Win'
                else:
                    result = 'Lose'
            await ctx.send(f'You {result}! you choose {rpschoice}, I choose {rpsgame}')
        else:
            await ctx.send(f"Please input correct argument. You should choose rock, paper or scissor")

    @commands.command(name="type", help="You wonder why this command exist")
    async def typing(self, ctx):
        await ctx.trigger_typing()

    @commands.command(name='tictactoe', help="Yes it is")
    async def tic_game(self, ctx, opponent: discord.User):
        if opponent == ctx.author:
            await ctx.send("Do you need friend?", delete_after=5)
            return
        if ctx.channel.id in occupied_channel:
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
        board = ["🟦" for b in range(9)]
        player_pos = {":one:": [],  ":two:": []}
        winner = ""
        done = False
        occupied_channel.add(ctx.channel.id)

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
            board[int(choice.content)-1] = cursor
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

        occupied_channel.remove(ctx.author.channel)
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
    async def guessing(self, ctx, difficulty: int = 1, max_attempt: int = None):
        if ctx.channel.id in occupied_channel:
            return
        multiplier_list = [2, 5, 10]
        if difficulty >= 69:
            multiplier_list.extend([100000, 500000])
        if difficulty >= 3:
            multiplier_list.extend([1000, 5000])
        if difficulty >= 2:
            multiplier_list.extend([50, 100, 500])
        min_number = random.randrange(1, 101, 10)
        multiplier = random.choice(multiplier_list)
        max_number = min_number * multiplier
        if not max_attempt:
            max_attempt = ceil(log(max_number-min_number+2, 2)) + 1
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

        occupied_channel.add(ctx.channel.id)
        while attempt <= max_attempt:
            try:
                guess = await self.bot.wait_for("message", check=valid_number, timeout=60)
            except asyncio.TimeoutError:
                await ctx.send("You don't guess in 1 minute. aborting")
                occupied_channel.remove(ctx.channel.id)
                return
            if int(guess.content) < selected_number:
                await ctx.send(f"**Low**, {max_attempt - attempt} left\n"
                               f"Range: {min_number} - {max_number}")
            elif int(guess.content) > selected_number:
                await ctx.send(f"**High**, {max_attempt - attempt} left\n"
                               f"Range: {min_number} - {max_number}")
            else:
                await ctx.send(f"Correct. Guessed in {attempt} attempt")
                occupied_channel.remove(ctx.channel.id)
                return
            attempt += 1
        occupied_channel.remove(ctx.channel.id)
        await ctx.send(f"You failed to guess. Correct: {selected_number}")

    @commands.command(name="osutop", help="Flex your recent osu play")
    async def get_osu(self, ctx, username):
        api_url = "https://osu.ppy.sh/api/v2"
        token_url = "https://osu.ppy.sh/oauth/token"
        message = await ctx.send("Connecting <a:discordloading:792012369168957450>")

        async def get_token():
            data = {
                "client_id": int(client_id),
                "client_secret": client_secret,
                "grant_type": "client_credentials",
                "scope": "public"
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(token_url, data=data) as response:
                    r = await response.json()
            return r

        raw = await get_token()
        token = raw["access_token"]
        headers = {
            "Content_Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
        params = {
            "mode": "osu",
            "limit": 5
        }
        async with aiohttp.ClientSession() as session1:
            async with session1.get(f"{api_url}/users/{username}", params=params, headers=headers) \
                    as response1:
                find_username = await response1.json()
                userid = find_username["id"]
                async with session1.get(f"{api_url}/users/{userid}/scores/best", params=params, headers=headers) \
                        as response2:
                    raw = await response2.json()
        custom_embed = discord.Embed(title=raw[0]["user"]["username"], description="Top 5 map")
        custom_embed.set_thumbnail(url=raw[0]["user"]["avatar_url"])
        for x in range(5):
            title = raw[x]["beatmapset"]["title"]
            title_url = raw[x]["beatmap"]["url"]
            statistic = raw[x]["statistics"]
            count_50, count_100, count_300 = statistic["count_50"], statistic["count_100"], statistic["count_300"]
            count_geki, count_katu, count_miss = statistic["count_geki"], statistic["count_katu"], statistic[
                "count_miss"]
            pp = raw[x]["pp"]
            difficulty_ver = raw[x]["beatmap"]["version"]
            difficulty_rating = raw[x]["beatmap"]["difficulty_rating"]
            accuracy = raw[x]["accuracy"]
            max_combo = raw[x]["max_combo"]
            mods = " ".join(raw[x]["mods"])
            custom_embed.add_field(name=f"{title} ⭐ {difficulty_rating}",
                                   value=f"[{difficulty_ver}]({title_url})\n"
                                         f"PP: {pp} | {round(accuracy * 100, 1)}% | {max_combo}x\n"
                                         f"Mod(s): {mods}\n"
                                         f"**300**: {count_300} | **100**: {count_100} | **50**: {count_50}\n"
                                         f"**激**: {count_geki} | **喝**: {count_katu} | **X**: {count_miss}",
                                   inline=False)
        await ctx.send(embed=custom_embed)
        await message.delete()


def setup(bot):
    bot.add_cog(Miscellaneous(bot))