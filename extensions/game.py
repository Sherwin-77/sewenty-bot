from __future__ import annotations

import discord
from discord.ext import commands
from discord import app_commands

import asyncio
from itertools import repeat
import random
from traceback import format_exception
from typing import Optional, Union, TYPE_CHECKING

from extensions.games.gelud import Hero, Battle
from extensions.games.gelud.game_system import weaponry
from extensions.games import minesweeper

from constants import CHARACTER_NAMES, CHAR_LIST

if TYPE_CHECKING:
    from main import SewentyBot

# mango_url = f"mongodb+srv://{EMAILS}:{PASSWORDS}@cluster0.kvwdz.mongodb.net/test"

list_weapon = list(weaponry.keys())

commandCooldown, battleCooldown, teamCooldown = {}, {}, {}

running_game = set()


async def update_point(userid, battle_point, cursor):
    """
    Update only the battle point of user

    Parameters
    ----------
    userid : int
        This must be discord user id
    battle_point : int
    cursor : motor.motor_asyncio.AsyncioIOMotorCollection

    Returns
    -------
    None
    """
    await cursor.update_one({"_id": str(userid)}, {"$set": {"battlepoint": battle_point}})


async def update_character(userid, char, weapon, hp, attack, speed, defense, attack1, speed1, ranges, defense1, passive,
                           description, battle_point, cursor):
    """
    Replace existing character of user in db

    Parameters
    ----------
    userid : int
         This must be discord user id
    char : int
    weapon : str
    hp : int
    attack : int
    speed : int
    defense : int
    attack1 : int
    speed1 : int
    ranges : int
    defense1 : int
    passive : str
    description : str
    battle_point : int
    cursor : motor.Motor_asyncio.AsyncioIOMotorCollection

    Returns
    -------
    None
    """
    userid = str(userid)
    await cursor.update_one({"_id": userid}, {"$set": {"char": char,
                                                       "weapon": weapon,
                                                       "hp": hp,
                                                       "attack": attack,
                                                       "speed": speed,
                                                       "defense": defense,
                                                       "attack1": attack1,
                                                       "speed1": speed1,
                                                       "range": ranges,
                                                       "defense1": defense1,
                                                       "passive": passive,
                                                       "description": description,
                                                       "battlepoint": battle_point}})


async def insert_character(userid, char, weapon, hp, attack, speed, defense, attack1, speed1, ranges, defense1, passive,
                           description, cursor):
    """
    Create character of user in db

    Parameters
    ----------
    userid : int
        This must be discord user id
    char : str
    weapon : str
    hp : int
    attack : int
    speed : int
    defense : int
    attack1 : int
    speed1 : int
    ranges : int
    defense1 : int
    passive : str
    description : str
    cursor : motor.motor_asyncio.AsyncIOMotorCollection

    Returns
    -------
    None
    """
    userid = str(userid)
    await cursor.insert_one({"_id": userid,
                             "char": char,
                             "weapon": weapon,
                             "hp": hp,
                             "attack": attack,
                             "speed": speed,
                             "defense": defense,
                             "attack1": attack1,
                             "speed1": speed1,
                             "range": ranges,
                             "defense1": defense1,
                             "passive": passive,
                             "description": description,
                             "battlepoint": 0})


def generate_enemy(stat, name, multiplier: float = 1):
    max_stat = 200
    weapon = random.choice(list_weapon)
    char = random.choice(CHAR_LIST)
    hp = random.randrange(30, 81)
    attack = random.randrange(30, 51 + (100 - hp))
    speed = random.randrange(1, 6)
    defense = max_stat - hp - attack - speed
    ranges = weaponry[weapon]['range']
    hp = round(((hp + stat) * 8) * multiplier)
    attack = round((attack + weaponry[weapon]['attack'] + stat) * multiplier)
    defense = round((defense + weaponry[weapon]['defense'] + stat) * multiplier)
    speed += weaponry[weapon]['speed']
    return Hero(name, char, weapon, hp, attack, speed, defense, ranges, weaponry[weapon]['passive'], None)


class User(Hero):
    def __init__(self, profile: dict, *, name: Optional[str] = None, battle_point: int = 0):
        self.profile = profile
        self.battle_point = battle_point
        if "battlepoint" in self.profile and self.battle_point == 0:
            self.battle_point = self.profile["battlepoint"]
        self.name = name
        self.char = self.profile['char']
        self.weapon = self.profile['weapon']
        self.hp = round(self.profile['hp'] * 8 * (1 + self.battle_point * 0.05))
        self.attack = round((self.profile['attack'] + self.profile['attack1']) * (1 + 0.05 * self.battle_point))
        self.speed = self.profile['speed'] + self.profile['speed1']
        self.defense = round((self.profile['defense'] + self.profile['defense1']) * (1 + 0.05 * self.battle_point))
        self.ranges = self.profile['range']
        self.passive = self.profile['passive']
        self.description = self.profile['description']
        super().__init__(self.name, self.char, self.weapon, self.hp, self.attack, self.speed, self.defense,
                         self.ranges, self.passive, self.description)

    def show(self):
        profile = self.profile
        char = self.char
        weapon = self.weapon
        battle_point = self.battle_point
        hp = profile['hp']
        attack = profile['attack']
        speed = profile['speed']
        defense = profile['defense']
        attack1 = profile['attack1']
        speed1 = profile['speed1']
        ranges = profile['range']
        defense1 = profile['defense1']
        passive = profile['passive']
        description = profile['description']
        custom_embed = discord.Embed(title='Profile',
                                     description=f'Your character: {char}\n'
                                                 f'HP: {hp}\n'
                                                 f'Attac: {attack}\n'
                                                 f'Spid: {speed}\n'
                                                 f'Difens: {defense}\n'
                                                 f'BettelPoint: {battle_point}',
                                     color=discord.Colour.yellow())
        custom_embed.add_field(name='Weapon', value=f'Your weapon: {weapon}\n'
                                                    f'Weapon Stat:\n'
                                                    f'Attac: {attack1}\n'
                                                    f'Spid: {speed1}\n'
                                                    f'Range: {ranges}\n'
                                                    f'Difens: {defense1}\n'
                                                    f'Passife {passive}\n'
                                                    f'{description}', inline=False)
        return custom_embed


class Team(Hero):
    def __init__(self, team: dict, *, name: str):
        self.team = team
        self.name = name
        self.hp, self.attack, self.speed, self.defense, self.ranges = [x for x in repeat(0, 5)]
        self.weapon = []
        self.description = ""
        for x in range(1, 4):
            char = self.team["team"][x]["char"]
            passive = self.team["team"][x]["passive"]
            self.hp += self.team["team"][x]["hp"]
            self.attack += self.team["team"][x]["attack"] + self.team["team"][x]["attack1"]
            self.speed += self.team["team"][x]["speed"] + self.team["team"][x]["speed1"]
            self.defense += self.team["team"][x]["defense"] + self.team["team"][x]["defense1"]
            self.ranges += self.team["team"][x]["ranges"]
            self.weapon.append(self.team["team"][x]["weapon"])
            self.description += f"{char} | {self.weapon[x - 1]} {passive}\n"
        self.weapon = list(set(self.weapon))
        self.hp *= 8
        self.speed //= 3
        self.ranges //= 3
        super(Team, self).__init__(self.name, None, self.weapon, self.hp, self.attack, self.speed, self.defense,
                                   self.ranges, None, self.description)


class MineCellButton(discord.ui.Button):
    def __init__(self, row: int, col: int):
        super().__init__(style=discord.ButtonStyle.blurple, label='\u200b', row=col)  # ah yes
        self.row = row
        self.col = col

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: MineBoard = self.view
        if not self.view.message:
            return
        if self.view.player.id != interaction.user.id:
            return await interaction.response.send_message("You are not the player :c", ephemeral=True)
        content = "Safe"
        if not view.started:
            view.start(row_position=self.row, column_position=self.col)
            view.started = True
            self.label = view.game.data[self.col][self.row]
        else:
            dead = view.game.open(row_position=self.row, column_position=self.col)
            if dead:
                content = "You step on bomb :c"
                self.style = discord.ButtonStyle.danger
                view.show_all()
            else:
                view.show_opened()
                if view.game.is_win():
                    view.show_all()
                    content = "You win :D"

        await interaction.response.edit_message(content=content, view=view)


class MineBoard(discord.ui.View):

    def __init__(self):
        super().__init__()
        self.started = False
        self.game = minesweeper.Minesweeper(5, 5)
        self.message = None
        self.player = None
        for i in range(5):
            for j in range(5):
                self.add_item(MineCellButton(i, j))

    def show_all(self):
        for button in self.children:
            button: MineCellButton
            col = button.col
            row = button.row
            if self.game.data[col][row] <= minesweeper.MINE_VALUE:
                button.emoji = "<:rekt:835656364864438282>"
            else:
                button.label = str(self.game.data[col][row] or '\u200b')
            button.disabled = True
        running_game.remove(str(self.player.id))
        self.stop()

    async def on_timeout(self) -> None:
        for button in self.children:
            button: MineCellButton
            button.disabled = True
        running_game.remove(str(self.player.id))
        await self.message.edit(view=self)

    def start(self, row_position, column_position):
        self.game.start(row_position=row_position, column_position=column_position)
        self.show_opened()

    def show_opened(self):
        for button in self.children:
            button: MineCellButton
            col = button.col
            row = button.row
            if self.game.visited[col][row] and self.game.data[col][row] >= 0:
                button.label = str(self.game.data[col][row] or '\u200b')
                button.disabled = True


class CustomGame(app_commands.Group, name="custombattle"):
    """
    Set your own battle
    """

    def __init__(self):
        super().__init__()

    @app_commands.command(name="solo")
    @app_commands.describe(weapon="Which weapon you want to use")
    @app_commands.choices(weapon=[
        app_commands.Choice(name=x[1:-1].replace('_', ' ').title(), value=x) for x in list_weapon
    ])
    async def solo_custom(self, interaction: discord.Interaction, weapon: app_commands.Choice[str]):
        await interaction.response.send_message(weapon.value, ephemeral=True)
        max_stat = 200
        hp = random.randrange(30, 81)
        attack = random.randrange(30, 51 + (100 - hp))
        speed = random.randrange(1, 6)
        defense = max_stat - hp - attack - speed
        player = Hero(name=interaction.user.name,
                      char=random.choice(CHAR_LIST),
                      weapon=weapon.value,
                      hp=hp * 8,
                      attack=attack + weaponry[weapon.value]["attack"],
                      speed=speed + weaponry[weapon.value]["speed"],
                      defense=defense + weaponry[weapon.value]["defense"],
                      ranges=weaponry[weapon.value]["range"],
                      passive=weaponry[weapon.value]['passive'],
                      description=weaponry[weapon.value]['description'])
        enemy = generate_enemy(0, random.choice(CHARACTER_NAMES), 1)
        system = Battle(player, enemy)
        log = 'Battle Started'
        custom_embed = discord.Embed(title='Battle',
                                     description=f'Your character: {player.char}\n'
                                                 f'HP: {player.hp}\n'
                                                 f'Attac: {player.attack}\n'
                                                 f'Spid: {player.speed}\n'
                                                 f'Difens: {player.defense}\n'
                                                 f'Range: {player.ranges}\n'
                                                 f'Weapon: {player.weapon}\n',
                                     color=discord.Colour.yellow())
        custom_embed.add_field(name='Enemy', value=f'Opponent character: {enemy.char}\n'
                                                   f'HP: {enemy.hp}\n'
                                                   f'Attac: {enemy.attack}\n'
                                                   f'Spid: {enemy.speed}\n'
                                                   f'Difens: {enemy.defense}\n'
                                                   f'Range: {enemy.ranges}\n'
                                                   f'Weapon: {enemy.weapon}\n')
        message = await interaction.followup.send(embed=custom_embed)
        custom_embed.add_field(name='Log', value=f'{log}', inline=False)
        battleCooldown.update({str(interaction.user.id): True})
        rounds = 0
        log = system.start()
        while True:
            custom_embed = discord.Embed(title=f'Battle round {rounds}',
                                         description=f'Your character: {player.char}\n'
                                                     f'HP: {player.hp}\n'
                                                     f'Attac: {player.attack}\n'
                                                     f'Spid: {player.speed}\n'
                                                     f'Difens: {player.defense}\n'
                                                     f'Range: {player.ranges}\n'
                                                     f'Weapon: {player.weapon}\n',
                                         color=discord.Colour.yellow())
            custom_embed.add_field(name='Enemy', value=f'Opponent character: {enemy.char}\n'
                                                       f'HP: {enemy.hp}\n'
                                                       f'Attac: {enemy.attack}\n'
                                                       f'Spid: {enemy.speed}\n'
                                                       f'Difens: {enemy.defense}\n'
                                                       f'Range: {enemy.ranges}\n'
                                                       f'Weapon: {enemy.weapon}\n')
            custom_embed.add_field(name='Log', value=f'{log}', inline=False)
            await asyncio.sleep(3)
            await message.edit(embed=custom_embed)

            rounds += 1

            if enemy.hp <= 0 or player.hp <= 0 or rounds > 20:
                if enemy.hp <= 0 or player.hp > enemy.hp:
                    await interaction.followup.send(f'{player.name} win!')

                else:
                    await interaction.followup.send(f'{enemy.name} win!')
                battleCooldown.pop(str(interaction.user.id))
                break
            log = system.process(rounds)


class SlashCommandGame(app_commands.Group, name="game"):
    def __init__(self):
        super().__init__()

    @app_commands.command(name="minesweeper")
    async def minesweeper(self, interaction: discord.Interaction):
        if str(interaction.user.id) in running_game:
            return await interaction.response.send_message("You have running game :c", ephemeral=True)

        game = MineBoard()
        await interaction.response.send_message("Game started", view=game)
        game.message = await interaction.original_response()
        game.player = interaction.user
        running_game.add(str(interaction.user.id))


class Game(commands.Cog):
    def __init__(self, bot: SewentyBot):
        self.bot: SewentyBot = bot

    @commands.command(aliases=["gamestart"])
    async def startgame(self, ctx, re_roll=None):
        """
        Interested in game?
        Add any word as a parameter for reroll existing account (Weapon and stat change)
        """
        userid = ctx.author.id
        query = {"_id": str(ctx.author.id)}
        if str(userid) in commandCooldown:
            return
        profile = await self.bot.GAME_COLLECTION.find_one(query)
        counts = await self.bot.GAME_COLLECTION.count_documents(query)
        if counts == 0 or re_roll == "reroll" or re_roll == "rr":
            weapon = random.choice(list_weapon)
            char = random.choice(CHAR_LIST)
            max_stat = 200
            hp = random.randrange(30, 81)
            attack = random.randrange(30, 51 + (100 - hp))
            speed = random.randrange(1, 6)
            defense = max_stat - hp - attack - speed
            attack1 = weaponry[weapon]['attack']
            speed1 = weaponry[weapon]['speed']
            ranges = weaponry[weapon]['range']
            defense1 = weaponry[weapon]['defense']
            passive = weaponry[weapon]['passive']
            description = weaponry[weapon]['description']
            custom_embed = discord.Embed(title='Game started',
                                         description=f'You get character: {char}\n'
                                                     f'HP: {hp}\n'
                                                     f'Attac: {attack}\n'
                                                     f'Spid: {speed}\n'
                                                     f'Difens: {defense}',
                                         color=discord.Colour.yellow())
            custom_embed.add_field(name='Weapon', value=f'You get: {weapon}\n'
                                                        f'Weapon Stat:\n'
                                                        f'Attac: {attack1}\n'
                                                        f'Spid: {speed1}\n'
                                                        f'Range: {ranges}\n'
                                                        f'Difens: {defense1}\n'
                                                        f'Passife {passive}\n'
                                                        f'{description}', inline=False)
            await ctx.send(embed=custom_embed)
            if counts != 0:  # keep battle point of user if exist
                battle_point = 0
                if "battlepoint" in profile:
                    battle_point = profile["battlepoint"]
                await update_character(userid, char, weapon, hp, attack, speed, defense,
                                       attack1, speed1, ranges, defense1,
                                       passive, description, battle_point, self.bot.GAME_COLLECTION)
            else:
                await insert_character(userid, char, weapon, hp, attack, speed, defense,
                                       attack1, speed1, ranges, defense1,
                                       passive, description, self.bot.GAME_COLLECTION)

        else:
            await ctx.send("You already start your game :c", delete_after=5)
        commandCooldown.update({str(userid): True})
        await asyncio.sleep(3)
        commandCooldown.pop(str(userid))

    @commands.command(aliases=["gameprofile", "profile"])
    async def profilegame(self, ctx, user: Optional[discord.User] = None):
        """
        Check for profile game
        """
        if not user:
            userid = ctx.author.id
        else:
            userid = user.id
        query = {"_id": str(userid)}
        if str(ctx.author.id) in commandCooldown:
            return
        counts = await self.bot.GAME_COLLECTION.count_documents(query)
        user_profile = await self.bot.GAME_COLLECTION.find_one(query)
        if counts != 0:
            player = User(user_profile)
            await ctx.send(embed=player.show())
        else:
            await ctx.send("You haven't started game :c", delete_after=5)
        commandCooldown.update({str(ctx.author.id): True})
        await asyncio.sleep(3)
        commandCooldown.pop(str(ctx.author.id))

    @commands.command()
    async def setpoint(self, ctx, point: int):
        """
        Set battle point (Can only run once when you have maxed point)
        """

        query = {"_id": str(ctx.author.id)}
        counts = await self.bot.GAME_COLLECTION.count_documents(query)
        if counts == 0:
            return await ctx.send("You haven't started your game :c", delete_after=3)
        profile = await self.bot.GAME_COLLECTION.find_one(query)
        if "battlepoint" not in profile:
            return await ctx.send("You don't have any battle point", delete_after=3)
        if profile["battlepoint"] < 2147483647:
            return await ctx.send("Your point is not maxed", delete_after=3)
        if point > 2147483647:
            return await ctx.send("Point is too large", delete_after=3)

        def custom_embed(color):
            return discord.Embed(title="Confirmation",
                                 description=f"are you sure want to set your point to {point}?",
                                 color=color)

        target = await ctx.send(embed=custom_embed(discord.Colour.yellow()))
        await target.add_reaction("✅")
        await target.add_reaction("❎")

        def check(reaction, users):
            return users == ctx.author and str(reaction.emoji) in ["✅", "❎"] and reaction.message == target

        try:
            emoji, user = await self.bot.wait_for("reaction_add", timeout=15, check=check)
        except asyncio.TimeoutError:
            await target.edit(embed=custom_embed(discord.Colour.red()))
            return
        if str(emoji.emoji) == "❎":
            await target.edit(embed=custom_embed(discord.Colour.red()))
            return
        await update_point(ctx.author.id, point, self.bot.GAME_COLLECTION)
        if "ascended" in profile:
            await target.edit(content="Success", embed=None)
            return
        await self.bot.GAME_COLLECTION.update_one({"_id": str(ctx.author.id)}, {"$set": {"ascended": True}})
        await target.edit(content=f"Success! {ctx.author.name} ascended and gained power to change weapon\n"
                                  f"`s!weaponset [weapon]`", embed=None)

    @commands.command(aliases=["setweapon"])
    async def weaponset(self, ctx, weapon: str):
        """
        Change your weapon. Ascended only
        """
        query = {"_id": str(ctx.author.id)}
        counts = self.bot.GAME_COLLECTION.count_documents(query)
        if counts == 0:
            return await ctx.send("You haven't started your game :c", delete_after=3)
        profile = await self.bot.GAME_COLLECTION.find_one(query)
        if "ascended" not in profile:
            return await ctx.send("Ascended only!", delete_after=3)
        if not profile["ascended"]:
            return await ctx.send("Something went wrong, please DM invalid-user#8807", delete_after=5)
        weapon = f":{weapon}:"
        if weapon not in list_weapon:
            return await ctx.send("Input valid weapon name `s!wdesc`", delete_after=3)
        attack1 = weaponry[weapon]['attack']
        speed1 = weaponry[weapon]['speed']
        ranges = weaponry[weapon]['range']
        defense1 = weaponry[weapon]['defense']
        passive = weaponry[weapon]['passive']
        description = weaponry[weapon]['description']
        await self.bot.GAME_COLLECTION.update_one({"_id": str(ctx.author.id)}, {"$set": {"weapon": weapon,
                                                                                         "attack1": attack1,
                                                                                         "speed1": speed1,
                                                                                         "range": ranges,
                                                                                         "defense1": defense1,
                                                                                         "passive": passive,
                                                                                         "description": description
                                                                                         }})
        profile = await self.bot.GAME_COLLECTION.find_one(query)
        player = User(profile)
        await ctx.send(embed=player.show())

    @commands.command(aliases=["gf", "fight", "bt"])
    async def gamefight(self, ctx, opponent: Union[discord.User, str], balance: Optional[bool] = False):
        """
        Battle with other player or bot
        Available difficulties are 'e', 'm', 'h', and 'i'
       """
        if str(ctx.author.id) in battleCooldown:
            return
        query = {"_id": str(ctx.author.id)}
        converter = commands.UserConverter()
        counts = await self.bot.GAME_COLLECTION.count_documents(query)
        if counts != 0:
            user_profile = await self.bot.GAME_COLLECTION.find_one(query)
            player = User(user_profile, name=ctx.author.name)
            battle_point = player.battle_point
        else:
            await ctx.send("You haven't started your game :c")
            return
        if opponent in {'e', 'm', 'h', 'i'}:
            if opponent == 'e':
                stat = 1
                add_streak = 1
            elif opponent == 'm':
                stat = 5
                add_streak = 2
            elif opponent == 'h':
                stat = 10
                add_streak = 4
            else:
                stat = 15
                add_streak = 5
            enemy = generate_enemy(stat, random.choice(CHARACTER_NAMES),
                                   1 + 0.5 * random.random() + 0.05 * battle_point)

        else:
            enemy_user = opponent
            if not isinstance(enemy_user, discord.User):
                enemy_user = await converter.convert(ctx, opponent)
            enemy_counts = await self.bot.GAME_COLLECTION.count_documents({"_id": str(enemy_user.id)})

            if enemy_counts != 0:
                name = enemy_user.name
                enemy_profile = await self.bot.GAME_COLLECTION.find_one({"_id": str(enemy_user.id)})
                add_streak = 0
                if balance:
                    enemy = User(enemy_profile, name=name, battle_point=player.battle_point)
                else:
                    enemy = User(enemy_profile, name=enemy_user.name)
            else:
                return await ctx.send("Player haven't started any game :c")
        system = Battle(player, enemy)
        log = "Battle Started"
        custom_embed = discord.Embed(title='Battle',
                                     description=f'Your character: {player.char}\n'
                                                 f'HP: {player.hp}\n'
                                                 f'Attac: {player.attack}\n'
                                                 f'Spid: {player.speed}\n'
                                                 f'Difens: {player.defense}\n'
                                                 f'Range: {player.ranges}\n'
                                                 f'Weapon: {player.weapon}\n',
                                     color=discord.Colour.yellow())
        custom_embed.add_field(name='Enemy', value=f'Opponent character: {enemy.char}\n'
                                                   f'HP: {enemy.hp}\n'
                                                   f'Attac: {enemy.attack}\n'
                                                   f'Spid: {enemy.speed}\n'
                                                   f'Difens: {enemy.defense}\n'
                                                   f'Range: {enemy.ranges}\n'
                                                   f'Weapon: {enemy.weapon}\n')
        message = await ctx.send(embed=custom_embed)
        custom_embed.add_field(name='Log', value=f'{log}', inline=False)
        battleCooldown.update({str(ctx.author.id): True})
        rounds = 0
        log = system.start()
        while True:
            custom_embed = discord.Embed(title=f'Battle round {rounds}',
                                         description=f'Your character: {player.char}\n'
                                                     f'HP: {player.hp}\n'
                                                     f'Attac: {player.attack}\n'
                                                     f'Spid: {player.speed}\n'
                                                     f'Difens: {player.defense}\n'
                                                     f'Range: {player.ranges}\n'
                                                     f'Weapon: {player.weapon}\n',
                                         color=discord.Colour.yellow())
            custom_embed.add_field(name='Enemy', value=f'Opponent character: {enemy.char}\n'
                                                       f'HP: {enemy.hp}\n'
                                                       f'Attac: {enemy.attack}\n'
                                                       f'Spid: {enemy.speed}\n'
                                                       f'Difens: {enemy.defense}\n'
                                                       f'Range: {enemy.ranges}\n'
                                                       f'Weapon: {enemy.weapon}\n')
            custom_embed.add_field(name='Log', value=f'{log}', inline=False)
            await asyncio.sleep(3)
            await message.edit(embed=custom_embed)

            rounds += 1

            if enemy.hp <= 0 or player.hp <= 0 or rounds > 20:
                if enemy.hp <= 0 or player.hp > enemy.hp:
                    battle_point += add_streak
                    await ctx.send(f'{player.name} win! Your Battle point: {battle_point}')
                    if battle_point >= 2147483647:
                        await ctx.send(f"{ctx.author.mention} Your battle point reached max\n"
                                       f"If you would like to reset you can do s!setpoint to any point you want "
                                       f"(below 2147483647)\n"
                                       f"Note: This command only usable if you have max point")
                        await update_point(ctx.author.id, 2147483647, self.bot.GAME_COLLECTION)
                    else:
                        await update_point(ctx.author.id, battle_point, self.bot.GAME_COLLECTION)

                else:
                    await ctx.send(f'{enemy.name} win!')
                battleCooldown.pop(str(ctx.author.id))
                break
            log = system.process(rounds)

    @commands.group(aliases=["team"], invoke_without_command=True)
    async def teamgame(self, ctx):
        """
        Show your in game team or create it if you don't have one
        """
        if str(ctx.author.id) in commandCooldown:
            return
        max_stat = 200
        team_hp, team_attack, team_speed, team_defense, team_ranges = [x for x in repeat(0, 5)]
        query = {"_id": f"team{ctx.author.id}"}
        counts = await self.bot.GAME_COLLECTION.count_documents(query)
        if counts == 0:
            team = [None, {}, {}, {}]
            for x in range(1, 4):
                team[x] = {}
                team[x]['char'] = random.choice(CHAR_LIST)
                team[x]['hp'] = random.randrange(30, 81)
                team[x]['attack'] = random.randrange(30, 51 + (
                        100 - team[x]['hp']))
                team[x]['speed'] = random.randrange(1, 6)
                team[x]['defense'] = max_stat - team[x]['hp'] - team[x]['attack'] - team[x]['speed']
                team[x]['weapon'] = random.choice(list_weapon)
                weapon = team[x]['weapon']
                team[x]['attack1'] = weaponry[weapon]['attack']
                team[x]['speed1'] = weaponry[weapon]['speed']
                team[x]['ranges'] = weaponry[weapon]['range']
                team[x]['defense1'] = weaponry[weapon]['defense']
                team[x]['passive'] = weaponry[weapon]['passive']
            await self.bot.GAME_COLLECTION.insert_one({"_id": f"team{ctx.author.id}", "team": team})
        team = await self.bot.GAME_COLLECTION.find_one(query)
        team_embed = discord.Embed(title=f'{ctx.author.name}\'s Team',
                                   description=None,
                                   color=discord.Colour.random())
        for x in range(1, 4):
            char = team['team'][x]['char']
            hp = team['team'][x]['hp']
            attack = team['team'][x]['attack']
            speed = team['team'][x]['speed']
            defense = team['team'][x]['defense']
            weapon = team['team'][x]['weapon']
            attack1 = team['team'][x]['attack1']
            speed1 = team['team'][x]['speed1']
            ranges = team['team'][x]['ranges']
            defense1 = team['team'][x]['defense1']
            passive = team['team'][x]['passive']

            team_embed.add_field(name=f'[{x}]', value=f'{char}\n'
                                                      f'Hp: {hp}\n'
                                                      f'Attac: {attack}\n'
                                                      f'Spid: {speed}\n'
                                                      f'Difens: {defense}\n'
                                                      f'**Weapon**: {weapon} | {passive}\n'
                                                      f'Attac: {attack1}\n'
                                                      f'Difens: {defense1}\n'
                                                      f'Spid: {speed1}\n'
                                                      f'Range: {ranges}', inline=True)
            team_hp += team["team"][x]["hp"]
            team_attack += team["team"][x]["attack"] + team["team"][x]["attack1"]
            team_defense += team["team"][x]["defense"] + team["team"][x]["defense1"]
            team_speed += team["team"][x]["speed"] + team["team"][x]["speed1"]
            team_ranges += team["team"][x]["ranges"]
        team_ranges = team_ranges // 3
        team_speed = team_speed // 3
        team_embed.description = f"Hp: {team_hp}  "\
                                 f"Attac: {team_attack}  "\
                                 f"Difens: {team_defense}  "\
                                 f"Spid: {team_speed}  "\
                                 f"Range: {team_ranges}"
        team_embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar)
        await ctx.send(embed=team_embed)
        commandCooldown.update({str(ctx.author.id): True})
        await asyncio.sleep(3)
        commandCooldown.pop(str(ctx.author.id))

    @teamgame.command(name="rr", aliases=["reroll"])
    async def team_re_roll(self, ctx, position: int):
        if position < 1 or position > 3:
            return await ctx.reply("Position must be between 1 and 3", mention_author=False, delete_after=5)
        max_stat = 200
        team_hp, team_attack, team_speed, team_defense, team_ranges = [x for x in repeat(0, 5)]
        query = {"_id": f"team{ctx.author.id}"}
        counts = await self.bot.GAME_COLLECTION.count_documents(query)
        if counts == 0:
            return await ctx.send("You don't have team. Create team by using teamgame command (without rr option)")
        team = await self.bot.GAME_COLLECTION.find_one(query)
        x = position
        team['team'][x]['char'] = random.choice(CHAR_LIST)
        team['team'][x]['hp'] = random.randrange(30, 81)
        team['team'][x]['attack'] = random.randrange(30, 51 + (
                100 - team['team'][x]['hp']))
        team['team'][x]['speed'] = random.randrange(1, 6)
        team['team'][x]['defense'] = (max_stat
                                      - team['team'][x]['hp']
                                      - team['team'][x]['attack']
                                      - team['team'][x]['speed'])
        team['team'][x]['weapon'] = random.choice(list_weapon)
        weapon = team['team'][x]['weapon']
        team['team'][x]['attack1'] = weaponry[weapon]['attack']
        team['team'][x]['speed1'] = weaponry[weapon]['speed']
        team['team'][x]['ranges'] = weaponry[weapon]['range']
        team['team'][x]['defense1'] = weaponry[weapon]['defense']
        team['team'][x]['passive'] = weaponry[weapon]['passive']
        await self.bot.GAME_COLLECTION.update_one(query, {"$set": {"team": team['team']}})
        for x in range(1, 4):
            team_hp = team_hp + team['team'][x]['hp']
            team_attack = team_attack + team['team'][x]['attack'] + team['team'][x]['attack1']
            team_defense = team_defense + team['team'][x]['defense'] + team['team'][x]['defense1']
            team_speed = team_speed + team['team'][x]['speed'] + team['team'][x]['speed1']
            team_ranges = team_ranges + team['team'][x]['ranges']
        await ctx.message.add_reaction('✅')

    @team_re_roll.error
    async def team_re_roll_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            return await ctx.reply("Please input position", mention_author=False, delete_after=5)
        if isinstance(error, commands.errors.BadArgument):
            return await ctx.reply(f"Please input correct parameter\n"
                                   f"```py\n{error}```", mention_author=False, delete_after=5)
        owner = await self.bot.fetch_user(436376194166816770)
        channel = await owner.create_dm()
        output = ''.join(format_exception(type(error), error, error.__traceback__))
        if len(output) > 2000:
            return print(output)
        await channel.send(f"Uncaught error in channel <#{ctx.channel.id}> command `{ctx.command}`\n"
                           f"```py\n"
                           f"{output}```")

    @commands.command(aliases=["raidboss"])
    async def bossraid(self, ctx, difficulty: str):
        """
        Raid some boss with your team and show your skill!
        """
        if str(ctx.author.id) in teamCooldown:
            return
        query = {"_id": f"team{ctx.author.id}"}
        counts = await self.bot.GAME_COLLECTION.count_documents(query)
        if counts == 0:
            return await ctx.send("You don't have team :c")
        stat_buff = {'e': 10,
                     'h': 20,
                     'i': 30}
        if difficulty not in stat_buff:
            return await ctx.send("Select difficulty e,h or i", delete_after=5)
        stat = stat_buff[difficulty]
        team_profile = await self.bot.GAME_COLLECTION.find_one(query)
        team = Team(team_profile, name=f"{ctx.author.name}'s Team")
        boss = generate_enemy(stat, random.choice(CHARACTER_NAMES), 3 + random.randint(0, 35) / 100)
        system = Battle(team, boss)
        log = "Battle started"
        raid = discord.Embed(title="Raid Boss", description="Round 0", color=discord.Colour.random())
        raid.add_field(name=team.name, value=f'{team.description}\n'
                                             f'Hp: {team.hp}  Attac: {team.attack}\n'
                                             f'Difens: {team.defense}\n'
                                             f'Spid: {team.speed}\n'
                                             f'Range: {team.ranges}', inline=True)
        raid.add_field(name=boss.name, value=f'{boss.char}  {boss.weapon}\n'
                                             f'Hp: {boss.hp}\n'
                                             f'Attac: {boss.attack}\n'
                                             f'Difens: {boss.defense}\n'
                                             f'Spid: {boss.speed}\n'
                                             f'Range: {boss.ranges}')
        raid.add_field(name='Logs', value=log, inline=False)
        message = await ctx.send(embed=raid)
        rounds = 0
        log = system.start()
        teamCooldown.update({str(ctx.author.id): True})
        while True:
            raid = discord.Embed(title="Raid Boss", description=f"Round {rounds} battle", color=discord.Colour.random())
            raid.add_field(name=team.name, value=f'{team.description}\n'
                                                 f'Hp: {team.hp}  Attac: {team.attack}\n'
                                                 f'Difens: {team.defense}\n'
                                                 f'Spid: {team.speed}\n'
                                                 f'Range: {team.ranges}', inline=True)
            raid.add_field(name=boss.name, value=f'{boss.char}  {boss.weapon}\n'
                                                 f'Hp: {boss.hp}\n'
                                                 f'Attac: {boss.attack}\n'
                                                 f'Difens: {boss.defense}\n'
                                                 f'Spid: {boss.speed}\n'
                                                 f'Range: {boss.ranges}')
            raid.add_field(name='Logs', value=log, inline=False)
            await asyncio.sleep(3)
            await message.edit(embed=raid)

            rounds += 1

            if boss.hp <= 0 or team.hp <= 0 or rounds > 20:
                if boss.hp <= 0 or team.hp > boss.hp:
                    await ctx.send("Your team won! <a:kittyhyper:742702283287953409>")
                else:
                    await ctx.send("Your team lost <a:crii:799610834769674252>")
                teamCooldown.pop(str(ctx.author.id))
                break
            log = system.process(rounds)

    @bossraid.error
    async def raid_on_errors(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            return await ctx.reply("Please input difficulty `e`,`h`, or `i`", mention_author=False, delete_after=5)
        owner = await self.bot.fetch_user(436376194166816770)
        channel = await owner.create_dm()
        output = ''.join(format_exception(type(error), error, error.__traceback__))
        if len(output) > 2000:
            return print(output)
        await channel.send(f"Uncaught error in channel <#{ctx.channel.id}> command `{ctx.command}`\n"
                           f"```py\n"
                           f"{output}```")

    @commands.command()
    async def teambattle(self, ctx, users: discord.User):
        """
        Battle with your friend's team
        """
        if str(ctx.author.id) in teamCooldown:
            return
        query = {"_id": f"team{ctx.author.id}"}
        user_query = {"_id": f"team{users.id}"}
        counts = await self.bot.GAME_COLLECTION.count_documents(query)
        user_counts = await self.bot.GAME_COLLECTION.count_documents(user_query)
        if counts == 0:
            return await ctx.send("You don't have team :c")
        if user_counts == 0:
            return await ctx.send("User doesn't have team :c")
        team_profile = await self.bot.GAME_COLLECTION.find_one(query)
        enemy_profile = await self.bot.GAME_COLLECTION.find_one(user_query)
        team = Team(team_profile, name=f"{ctx.author.name}'s team")
        enemy = Team(enemy_profile, name=f"{users.name}'s team")
        system = Battle(team, enemy)

        log = "Battle started"
        raid = discord.Embed(title="Raid enemy", description="Round 0", color=discord.Colour.random())
        raid.add_field(name=team.name, value=f'{team.description}\n'
                                             f'Hp: {team.hp}\n'
                                             f'Attac: {team.attack}\n'
                                             f'Difens: {team.defense}\n'
                                             f'Spid: {team.speed}\n'
                                             f'Range: {team.ranges}')
        raid.add_field(name=enemy.name, value=f'{enemy.description}\n'
                                              f'Hp: {enemy.hp}\n'
                                              f'Attac: {enemy.attack}\n'
                                              f'Difens: {enemy.defense}\n'
                                              f'Spid: {enemy.speed}\n'
                                              f'Range: {enemy.ranges}')
        raid.add_field(name='Logs', value=log, inline=False)
        message = await ctx.send(embed=raid)
        rounds = 0
        log = system.start()
        teamCooldown.update({str(ctx.author.id): True})

        # let's begin our date
        while True:
            raid = discord.Embed(title='Raid enemy',
                                 description=f'Round {rounds} battle',
                                 color=discord.Colour.random())
            raid.add_field(name=team.name, value=f'{team.description}\n'
                                                 f'Hp: {team.hp}\n'
                                                 f'Attac: {team.attack}\n'
                                                 f'Difens: {team.defense}\n'
                                                 f'Spid: {team.speed}\n'
                                                 f'Range: {team.ranges}')
            raid.add_field(name=enemy.name, value=f'{enemy.description}\n'
                                                  f'Hp: {enemy.hp}\n'
                                                  f'Attac: {enemy.attack}\n'
                                                  f'Difens: {enemy.defense}\n'
                                                  f'Spid: {enemy.speed}\n'
                                                  f'Range: {enemy.ranges}')
            raid.add_field(name='Logs', value=log, inline=False)
            await asyncio.sleep(3)
            await message.edit(embed=raid)

            rounds += 1

            if enemy.hp <= 0 or team.hp <= 0 or rounds > 20:
                if enemy.hp <= 0 or team.hp > enemy.hp:
                    await ctx.send(f'{team.name} won! <a:kittyhyper:742702283287953409>')
                else:
                    await ctx.send(f'{enemy.name} won <a:crii:799610834769674252>')
                teamCooldown.pop(str(ctx.author.id))
                break
            log = system.process(rounds)

    @teambattle.error
    async def teambattle_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            return await ctx.reply("who you wanna battle with? (userid works instead mention)",
                                   mention_author=False,
                                   delete_after=5)
        owner = await self.bot.fetch_user(436376194166816770)
        channel = await owner.create_dm()
        output = ''.join(format_exception(type(error), error, error.__traceback__))
        if len(output) > 2000:
            return print(output)
        await channel.send(f"Uncaught error in channel <#{ctx.channel.id}> command `{ctx.command}`\n"
                           f"```py\n"
                           f"{output}```")

    @commands.command()
    async def wdesc(self, ctx, name=None):
        """
        Description about weapon in game
        """
        if not name:
            weapons = " | ".join(list_weapon)
            custom_embed = discord.Embed(title="Weapon List", description=weapons)
            custom_embed.set_footer(text="For specific weapon description, the name is the same as emoji name")
            await ctx.send(embed=custom_embed)
            return
        name = f":{name}:"
        if name not in weaponry:
            await ctx.send("Input weapon name when", delete_after=5)
            return
        attack = weaponry[name]["attack"]
        speed = weaponry[name]["speed"]
        ranges = weaponry[name]["range"]
        defense = weaponry[name]["defense"]
        passive = weaponry[name]["passive"]
        description = weaponry[name]['description']
        dexed = discord.Embed(title=name, description=f"Attac: {attack}\n"
                                                      f"Difens: {defense}\n"
                                                      f"Range: {ranges}\n"
                                                      f"Spid: {speed}\n"
                                                      f"Passife: {passive}\n"
                                                      f"{description}", color=discord.Colour.random())
        await ctx.send(embed=dexed)

    @commands.command(aliases=["guidegame", "startguide", "guidestart"])
    async def gameguide(self, ctx):
        """
        Get started
        """
        embed = discord.Embed(title='Game Guide', description='Need more help? ask @invalid-user#8807')
        embed.add_field(name='Start your game', value='This game has 2 mode. team and solo\n'
                                                      'Get your solo character by `startgame` command.'
                                                      'Not satisfied with your weapon? you can do `startgame reroll`\n'
                                                      'Get your team by `teamgame` command.'
                                                      'Not satisfied with your weapon combination? you can do '
                                                      '`teamgame rr [position]`')
        embed.add_field(name='Weapon', value='Every character you rolled get random weapon. You can check its passive '
                                             'by `wdesc [weapon]` command where weapon name as emoji name. '
                                             '**Note that same passive can\'t be stacked**')
        embed.add_field(name='Battle', value='For solo battle you can do `gamefight [difficulty/player]`. '
                                             'Difficulties for solo are e, m, h, i. '
                                             'You get **battlepoint** by winning battle'
                                             'which will boost your stat\n'
                                             'For team battle you can do `teambattle [player]` or you can raid '
                                             '`bossraid [difficulty]`. Difficulties for raid are e, h, i')
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar)
        await ctx.send(embed=embed)


async def setup(bot: SewentyBot):
    bot.tree.add_command(CustomGame(), guild=discord.Object(id=714152739252338749))
    bot.tree.add_command(SlashCommandGame())
    await bot.add_cog(Game(bot))
