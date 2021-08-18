import discord
from discord.ext import commands
from pymongo import MongoClient
from itertools import repeat
import math
import os
import random
import asyncio

emails = os.getenv('EMAIL')
passwords = os.getenv('PASSWORD')
mango_url = f'mongodb+srv://{emails}:{passwords}@clusterdiscord.8dm0p.mongodb.net/test'
cluster = MongoClient(mango_url)
game = cluster["game"]["data"]

weaponry = {':bow_and_arrow:': {'attack': 37, 'speed': 6, 'range': 26, 'defense': 16,
                                'passive': ':dart:',
                                'description': '**Archery**: Deal 50% more damage in ranged mode'},
            ':dagger:': {'attack': 46, 'speed': 20, 'range': 1, 'defense': 18,
                         'passive': ':dash:',
                         'description': '**Dodge**: Gain 130% of speed as dodge chance'},
            ':axe:': {'attack': 52, 'speed': 2, 'range': 2, 'defense': 24,
                      'passive': ':drop_of_blood:',
                      'description': '**Lifestyle**: heal you 50% of damage'},
            ':pick:': {'attack': 32, 'speed': 5, 'range': 1, 'defense': 54,
                       'passive': ':tools:',
                       'description': '**Baccstab**: Decreasing enemy def by 70% and your def by 10%'},
            ':magic_wand:': {'attack': 36, 'speed': 4, 'range': 10, 'defense': 36,
                             'passive': ':radioactive:',
                             'description': '**Chemical**: Deal 9% of enemy\'s current HP '
                                            'and heal by the damage dealt'},
            ':broom:': {'attack': 35, 'speed': 7, 'range': 2, 'defense': 41,
                        'passive': ':trident:',
                        'description': '**Theft**: Steal 30% of enemy defense and attack. additionally,'
                                       ' 20% chance to trigger again'},
            ':door:': {'attack': 26, 'speed': 2, 'range': 4, 'defense': 52,
                       'passive': ':shield:',
                       'description': '**Thicc door**: Increase 85% defense. If your hp below enemy,'
                                      'Increase def by 6%'},
            ':bomb:': {'attack': 50, 'speed': 4, 'range': 17, 'defense': 14,
                       'passive': ':boom:',
                       'description': '**Eksplosion**: Deal 80% of your attack as True Damage to enemy '
                                      'and decrease def by 10% every 5 rounds'},
            ':game_die:': {'attack': 30, 'speed': 5, 'range': 1, 'defense': 30,
                           'passive': '<:lucc:796732732113682442>',
                           'description': '**Lucc Dice**: Roll 6 sided dice and increase hp atk and def by '
                                          '8.5x of rolled dice'},
            ':gun:': {'attack': 30, 'speed': 6, 'range': 23, 'defense': 16,
                      'passive': ':microscope:',
                      'description': '**Precision**: Increase 3% crit chance and 5% crit dmg based on round'},
            ':satellite:': {'attack': 33, 'speed': 2, 'range': 4, 'defense': 45,
                            'passive': ':satellite_orbital:',
                            'description': '**Radar**: Decrease incoming attack by 45% for every odd round'},
            ':loudspeaker:': {'attack': 46, 'speed': 4, 'range': 1, 'defense': 32,
                              'passive': ':beginner:',
                              'description': '**Motivesien**: While your hp is lower than enemy, increase atk by 18%'},
            ':firecracker:': {'attack': 68, 'speed': 3, 'range': 3, 'defense': 10,
                              'passive': ':fireworks:',
                              'description': '**Fataliti**: Every round, 30% chance to deal fatality '
                                             '(45% if your hp is below enemy), Sacrifice your 5% def and '
                                             'dealing 25-40% (40-55% if your hp below enemy)'
                                             ' of your atk as well as '
                                             'decreasing enemy def by 25-40% of your atk '
                                             '(enemy def can\'t be lower than your def).\n'
                                             'If this fails, decrease your atk by 8% and increase def by 8%'}
            }

list_weapon = list(weaponry.keys())

char_list = [':man_walking:', ':woman_walking:', ':person_running:', ':woman_running:', ':sloth:',
             ':cat2:', ':dog2:', ':unicorn:', ':snail:', '<:snale:770847330600484864>', ':t_rex:',
             '<:EB_nekocute:780408575784255538>', ':wolf:', "<:MoriOwO:832762779450081312>",
             '<a:kittyrawr:719122783828967455>', '<a:kittymad:720191651175333898>',
             '<:babycuddle:751985441653391440>', '<:blobsob:809721186966831105>', ':snake:']

random_name = ["Ghost slayer", "Death mire", "P", "Yejing", "Skull grim", "Barrel", "Dark eye", "Vinii", "Dio",
               "Monno", "Not slime", "Paul", "Fenrir"]

owoCooldown, battleCooldown, teamCooldown = {}, {}, {}


def update_point(userid, battlepoint):
    game.update_one({"_id": str(userid)}, {"$set": {"battlepoint": battlepoint}})


def update_character(userid, char, weapon, hp, attack, speed, defense, attack1, speed1, ranges, defense1, passive,
                     description, battlepoint):
    userid = str(userid)
    game.update_one({"_id": userid}, {"$set": {"char": char,
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
                                               "battlepoint": battlepoint}})


def insert_character(userid, char, weapon, hp, attack, speed, defense, attack1, speed1, ranges, defense1, passive,
                     description):
    userid = str(userid)
    game.insert_one({"_id": userid,
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
    char = random.choice(char_list)
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


class Hero:
    def __init__(self, name, char, weapon, hp, attack, speed, defense, ranges, passive, description):
        self.name = name
        self.char = char
        self.weapon = weapon
        self.hp = hp
        self.attack = attack
        self.speed = speed
        self.defense = defense
        self.ranges = ranges
        self.passive = passive
        self.description = description
        self.power = 0
        self.is_ranged = False

    def set_power(self, target):
        if not isinstance(target, Hero):
            raise TypeError("Unexpected Type to attack")
        self.power = round(self.attack * math.exp(-target.defense / (self.attack + target.defense * 0.5)))

    def attacks(self, target, rounds, distance):
        if not isinstance(target, Hero):
            raise TypeError("Unexpected Type to attack")
        log = ""

        # critical and precision
        critical = False
        if ":gun:" in self.weapon:
            if self.chance(0.01 + 0.03 * rounds):
                self.power = round(self.power * (2 + 0.05 * rounds))
                critical = True
        else:
            if self.chance(0.01):
                self.power *= 2
                critical = True

        # endurance
        if ":satellite:" in target.weapon and rounds % 2 == 1:
            self.power -= round(self.power * 0.450)

        # fatality
        if ":firecracker:" in self.weapon:
            if self.chance(0.3 + (0.15 if self.hp < target.hp else 0)):
                delimiter = random.randint(0, 15) / 100
                damage_bound = 0.55 if self.hp <= target.hp else 0.4
                self.defense -= round(self.defense * 0.05)
                target.hp -= round((damage_bound - delimiter) * self.attack)
                target.defense -= round((0.4 - delimiter) * self.attack) if target.defense > self.defense else 0
                log += f"{self.name} deals **fatality** dmg, " \
                       f"dealing **{round((damage_bound - delimiter) * self.attack)}** " \
                       f"dmg as well as decreasing {target.name} def by " \
                       f"{round((0.4 - delimiter) * 100)}% of your atk\n"
            else:
                self.attack -= round(0.08 * self.attack)
                self.defense += round(0.08 * self.defense)
                log += f"{self.name} fails to deal fatality\n"

        # evasion and core atk
        if ":dagger:" in target.weapon and target.chance(target.speed * 0.013):
            if target.speed == 77:
                log += f"{target.name} bonk {self.name}, dealing **{target.attack ** 10}** damage. Jk lol\n"
            log += f"{target.name} dodge attack and take no damage"
        else:
            target.hp -= self.power
            log += (f"{self.name} have enough range at **{distance}** hyper meter and"
                    if self.is_ranged else self.name) \
                + f" deal **{self.power}** damage to {target.name}"
            if ":axe:" in self.weapon:
                self.hp += round(self.power * 0.50)
                log += f" and heal itself {round(self.power * 0.50)} hp"
            log += " **CRITICAL HIT**" if critical else ""

        # wand
        if ":magic_wand:" in self.weapon and target.hp > 0:
            self.hp += round(target.hp * 0.09 / 2) if self.hp >= target.hp else round(target.hp * 0.09)
            target.hp -= round(target.hp * 0.09)
            log = f"{log}\n" \
                  f"{self.name} deal damage 9% of {target.name} hp and heal itself"
        return log.strip()

    @staticmethod
    def chance(set_chance):
        return random.random() <= set_chance


class User(Hero):
    def __init__(self, user_id, name, battlepoint=0):
        self.profile = game.find_one({'_id': str(user_id)})
        self.battlepoint = battlepoint
        if "battlepoint" in self.profile and self.battlepoint == 0:
            self.battlepoint = self.profile['battlepoint']
        self.name = name
        self.user_id = user_id
        self.char = self.profile['char']
        self.weapon = self.profile['weapon']
        self.hp = round(self.profile['hp'] * 8 * (1 + self.battlepoint * 0.05))
        self.attack = round((self.profile['attack'] + self.profile['attack1']) * (1 + 0.05 * self.battlepoint))
        self.speed = self.profile['speed'] + self.profile['speed1']
        self.defense = round((self.profile['defense'] + self.profile['defense1']) * (1 + 0.05 * self.battlepoint))
        self.ranges = self.profile['range']
        self.passive = self.profile['passive']
        self.description = self.profile['description']
        super().__init__(self.name, self.char, self.weapon, self.hp, self.attack, self.speed, self.defense,
                         self.ranges, self.passive, self.description)

    def show(self):
        yellow = 0xfff00
        profile = self.profile
        char = self.char
        weapon = self.weapon
        battlepoint = self.battlepoint
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
                                                 f'BettelPoint: {battlepoint}',
                                     color=yellow)
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
    def __init__(self, user_id, name):
        self.team = game.find_one({"_id": f'team{user_id}'})
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


class Battle:
    def __init__(self, allies, enemy):
        self.allies = allies
        self.enemy = enemy
        self.distance = allies.ranges + enemy.ranges + allies.speed + enemy.speed

    def start(self):
        log = ""
        for weapon in ([self.allies.weapon] if isinstance(self.allies.weapon, str) else self.allies.weapon):
            if weapon == ':door:':
                self.allies.defense += round(self.allies.defense * 0.85)
                log += f'\n{self.allies.name} using :shield: buffing defense by 85%'
            elif weapon == ':broom:':
                self.allies.attack += round(self.enemy.attack * 0.30)
                self.allies.defense += round(self.enemy.defense * 0.30)
                log += f'\n{self.allies.name} using :trident: buffing itself by 30% ' \
                       f'{self.enemy.name} attack and defense'
            elif weapon == ':game_die:':
                rolled_number = random.randint(1, 6)
                self.allies.attack += round(self.allies.attack * 0.085 * rolled_number)
                self.allies.hp += round(self.allies.hp * 0.085 * rolled_number)
                self.allies.defense += round(self.allies.defense * 0.085 * rolled_number)
                log = log + f'\n{self.allies.name} rolled dice and get **{rolled_number}**. ' \
                            f'Increase stat by {rolled_number * 8.5}%'
            elif weapon == ':pick:':
                self.enemy.defense -= round(self.enemy.defense * 0.7)
                self.allies.defense -= round(self.allies.defense * 0.1)
                log += f'\n{self.allies.name} using :tools: decreasing {self.enemy.name} def by 70% and ' \
                       f'{self.allies.name} defense by 10%'

        for weapon in ([self.enemy.weapon] if isinstance(self.enemy.weapon, str) else self.enemy.weapon):
            if weapon == ':door:':
                self.enemy.defense += round(self.enemy.defense * 0.85)
                log += f'\n{self.enemy.name} using :shield: buffing defense by 85%'
            elif weapon == ':broom:':
                self.enemy.attack += round(self.allies.attack * 0.30)
                self.enemy.defense += round(self.allies.defense * 0.30)
                log += f'\n{self.enemy.name} using :trident: buffing itself by 30% ' \
                       f'{self.allies.name} attack and defense'
            elif weapon == ':game_die:':
                rolled_number = random.randint(1, 6)
                self.enemy.attack += round(self.enemy.attack * 0.085 * rolled_number)
                self.enemy.hp += round(self.enemy.hp * 0.085 * rolled_number)
                self.enemy.defense += round(self.enemy.defense * 0.085 * rolled_number)
                log += f'\n{self.enemy.name} rolled dice and get **{rolled_number}**. ' \
                       f'Increase stat by {rolled_number * 8.5}%'
            elif weapon == ':pick:':
                self.allies.defense -= round(self.allies.defense * 0.7)
                self.enemy.defense -= round(self.enemy.defense * 0.1)
                log += f'\n{self.enemy.name} using :tools: decreasing {self.allies.name} def by 70% and ' \
                       f'{self.enemy.name} defense by 10%'

        return log.strip() if log else "No early active weapon"

    def process(self, rounds):
        log = ""

        # bomb
        if ":bomb:" in self.allies.weapon and rounds % 5 == 1:
            self.enemy.hp -= round(self.allies.attack * 0.8)
            self.enemy.defense -= round(self.enemy.defense * 0.1)
            log = f'{self.allies.name} explode bomb and deal {round(self.allies.attack * 0.8)} damage to ' \
                  f'{self.enemy.name} and decrease def by 10%'
        if ":bomb:" in self.enemy.weapon and rounds % 6 == 1:
            self.allies.hp -= round(self.enemy.attack * 0.8)
            self.allies.defense -= round(self.allies.defense * 0.1)
            log = f'\n{self.allies.name} explode bomb and deal {round(self.allies.attack * 0.8)} damage to ' \
                  f'{self.enemy.name} and decrease def by 10%'

        # trigger broom
        if ":broom:" in self.allies.weapon and self.allies.chance(0.2):
            self.allies.attack += round(self.enemy.attack * 0.30)
            self.allies.defense += round(self.enemy.defense * 0.30)
            log += f'\n{self.allies.name} using :trident: buffing itself by 30% ' \
                   f'{self.enemy.name} attack and defense'

        if ":broom:" in self.enemy.weapon and self.enemy.chance(0.2):
            self.enemy.attack += round(self.allies.attack * 0.30)
            self.enemy.defense += round(self.allies.defense * 0.30)
            log += f'\n{self.enemy.name} using :trident: buffing itself by 30% ' \
                   f'{self.allies.name} attack and defense'

        # loudspeaker
        if ':loudspeaker:' in self.allies.weapon and self.allies.hp < self.enemy.hp:
            self.allies.attack += round(self.allies.attack * 0.18)
        if ':loudspeaker:' in self.enemy.weapon and self.enemy.hp < self.enemy.hp:
            self.enemy.attack += round(self.enemy.attack * 0.18)

        # door
        if ':door:' in self.allies.weapon and self.allies.hp < self.enemy.hp:
            self.allies.defense += round(self.allies.defense * 0.06)
        if ':door:' in self.enemy.weapon and self.enemy.hp < self.enemy.hp:
            self.enemy.defense += round(self.enemy.defense * 0.06)

        # before start, we set the power/damage
        self.allies.set_power(self.enemy)
        self.enemy.set_power(self.allies)

        while self.distance > self.allies.ranges and self.distance > self.enemy.ranges:
            # both out of range so we move position of both side by their speed
            self.distance -= self.allies.speed + self.enemy.speed
        if self.allies.ranges >= self.distance and self.enemy.ranges >= self.distance:
            # in melee mode
            self.allies.is_ranged, self.enemy.is_ranged = False, False
            if self.allies.speed >= self.enemy.speed:
                # allies has faster speed
                log += f"\n{self.allies.attacks(self.enemy, rounds, self.distance)}"
                if self.enemy.hp > 0:  # strike back
                    log += f"\n{self.enemy.attacks(self.allies, rounds, self.distance)}"
            else:
                # enemy has faster speed
                log += f"\n{self.enemy.attacks(self.allies, rounds, self.distance)}"
                if self.allies.hp > 0:  # strike back
                    log += f"\n{self.allies.attacks(self.enemy, rounds, self.distance)}"

        elif self.allies.ranges >= self.distance >= self.enemy.ranges:
            # allies in ranged mode while enemy is chasing
            self.allies.is_ranged = True
            self.enemy.is_ranged = False
            if ':bow_and_arrow:' in self.allies.weapon:
                self.allies.power += round(self.allies.power * 0.5)
            log += f"\n{self.allies.attacks(self.enemy, rounds, self.distance)}"
            self.distance = self.distance - self.enemy.speed

        else:
            # enemy is ranged mode while allies is chasing
            self.allies.is_ranged = False
            self.enemy.is_ranged = True
            if ':bow_and_arrow:' in self.enemy.weapon:
                self.enemy.power += round(self.enemy.power * 0.5)
            log += f"\n{self.enemy.attacks(self.allies, rounds, self.distance)}"
            self.distance = self.distance - self.allies.speed

        # compensation for ranged
        if self.distance + self.enemy.speed <= self.enemy.speed:
            self.distance = self.distance + round(self.enemy.speed / 4)
        elif self.distance + self.allies.speed <= self.allies.ranges:
            self.distance = self.distance + round(self.allies.speed / 4)

        return log.strip()


class Game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='startgame', help='interested in bot game?', aliases=['gamestart'])
    async def creategem(self, ctx, reroll=None):
        yellow = 0xfff00
        userid = ctx.author.id
        if str(userid) in owoCooldown:
            return
        profile = game.find_one({'_id': str(ctx.author.id)})
        if game.count_documents({"_id": str(userid)}) == 0 or reroll == 'reroll' or reroll == 'rr':
            weapon = random.choice(list_weapon)
            char = random.choice(char_list)
            maxstat = 200
            hp = random.randrange(30, 81)
            attack = random.randrange(30, 51 + (100 - hp))
            speed = random.randrange(1, 6)
            defense = maxstat - hp - attack - speed
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
                                         color=yellow)
            custom_embed.add_field(name='Weapon', value=f'You get: {weapon}\n'
                                                        f'Weapon Stat:\n'
                                                        f'Attac: {attack1}\n'
                                                        f'Spid: {speed1}\n'
                                                        f'Range: {ranges}\n'
                                                        f'Difens: {defense1}\n'
                                                        f'Passife {passive}\n'
                                                        f'{description}', inline=False)
            await ctx.send(embed=custom_embed)
            if game.count_documents({"_id": str(userid)}) != 0:
                battlepoint = 0
                if 'battlepoint' in profile:
                    battlepoint = profile['battlepoint']
                update_character(userid, char, weapon, hp, attack, speed, defense, attack1, speed1, ranges, defense1,
                                 passive, description, battlepoint)
            else:
                insert_character(userid, char, weapon, hp, attack, speed, defense, attack1, speed1, ranges, defense1,
                                 passive, description)

        else:
            await ctx.send('You already start your game :c', delete_after=5)
        owoCooldown.update({str(userid): True})
        await asyncio.sleep(3)
        owoCooldown.pop(str(userid))

    @commands.command(name='profilegame', help='Check your profile', aliases=['gameprofile'])
    async def checkgem(self, ctx, user: discord.User = None):
        if not user:
            userid = ctx.author.id
        else:
            userid = user.id
        if str(ctx.author.id) in owoCooldown:
            return
        if game.count_documents({'_id': str(userid)}) != 0:
            player = User(ctx.author.id, None)
            await ctx.send(embed=player.show())
        else:
            await ctx.send('You havent started game :c', delete_after=5)
        owoCooldown.update({str(ctx.author.id): True})
        await asyncio.sleep(3)
        owoCooldown.pop(str(ctx.author.id))

    @commands.command(name="setpoint", help="Set your battle point")
    async def set_point(self, ctx, point: int):
        if game.count_documents({"_id": str(ctx.author.id)}) == 0:
            await ctx.send("You haven't started your game :c", delete_after=3)
            return
        profile = game.find_one({'_id': str(ctx.author.id)})
        if "battlepoint" not in profile:
            await ctx.send("You don't have any battle point", delete_after=3)
            return
        if profile["battlepoint"] < 2147483647:
            await ctx.send("Your point is not maxed", delete_after=3)
            return
        if point > 2147483647:
            await ctx.send("Point is too large", delete_after=3)
            return
        yellow = 0xfff00
        red = 0x8b0000

        def custom_embed(color):
            return discord.Embed(title="Confirmation",
                                 description=f"are you sure want to set your point to {point}?",
                                 color=color)

        target = await ctx.send(embed=custom_embed(yellow))
        await target.add_reaction("✅")
        await target.add_reaction("❎")

        def check(reaction, users):
            return users == ctx.author and str(reaction.emoji) in ["✅", "❎"] and reaction.message == target

        try:
            emoji, user = await self.bot.wait_for("reaction_add", timeout=15, check=check)
        except asyncio.TimeoutError:
            await target.edit(embed=custom_embed(red))
            return
        if str(emoji.emoji) == "❎":
            await target.edit(embed=custom_embed(red))
            return
        update_point(ctx.author.id, point)
        if "ascended" in profile:
            await target.edit(content="Success", embed=None)
            return
        game.update_one({"_id": str(ctx.author.id)}, {"$set": {"ascended": True}})
        await target.edit(content=f"Success. {ctx.author.name} ascended and gained power to change weapon\n"
                                  f"`s!weaponset [weapon]`", embed=None)

    @commands.command(name="weaponset", help="Change your weapon. Ascended only", aliases=["setweapon"])
    async def change_weapon(self, ctx, weapon: str):
        if game.count_documents({"_id": str(ctx.author.id)}) == 0:
            await ctx.send("You haven't started your game :c", delete_after=3)
            return
        profile = game.find_one({'_id': str(ctx.author.id)})
        if "ascended" not in profile:
            await ctx.send("Ascended only!", delete_after=3)
            return
        if not profile["ascended"]:
            await ctx.send("Something went wrong, please DM invalid-user#8807", delete_after=5)
            return
        weapon = f":{weapon}:"
        if weapon not in list_weapon:
            await ctx.send("Input valid weapon name `s!wdesc`", delete_after=3)
            return
        attack1 = weaponry[weapon]['attack']
        speed1 = weaponry[weapon]['speed']
        ranges = weaponry[weapon]['range']
        defense1 = weaponry[weapon]['defense']
        passive = weaponry[weapon]['passive']
        description = weaponry[weapon]['description']
        game.update_one({"_id": str(ctx.author.id)}, {"$set": {"weapon": weapon,
                                                               "attack1": attack1,
                                                               "speed1": speed1,
                                                               "range": ranges,
                                                               "defense1": defense1,
                                                               "passive": passive,
                                                               "description": description
                                                               }})
        player = User(ctx.author.id, None)
        await ctx.send(embed=player.show())

    @commands.command(name='gamefight', help='Battle your character', aliases=['gf', 'fight', 'bt'])
    async def fighting(self, ctx, userid, balance=None):
        if str(ctx.author.id) in battleCooldown:
            return

        yellow = 0xfff00
        userid = (((userid.replace('<', '')).replace('>', '')).replace('@', '')).replace('!', '')
        if game.count_documents({'_id': str(ctx.author.id)}) != 0:
            player = User(ctx.author.id, ctx.author.name)
            battlepoint = player.battlepoint
        else:
            await ctx.send('You havent started your game :c')
            return
        if userid == 'e' or userid == 'm' or userid == 'h' or userid == 'i':
            if userid == 'e':
                stat = 1
                add_streak = 1
            elif userid == 'm':
                stat = 5
                add_streak = 2
            elif userid == 'h':
                stat = 10
                add_streak = 4
            else:
                stat = 15
                add_streak = 5
            enemy = generate_enemy(stat, random.choice(random_name), 1 + 0.5 * random.random() + 0.05 * battlepoint)

        else:
            if game.count_documents({'_id': str(userid)}) != 0:
                name = await self.bot.fetch_user(int(userid))
                name = name.name
                add_streak = 0
                if balance:
                    enemy = User(userid, name, player.battlepoint)
                else:
                    enemy = User(userid, name)
            else:
                await ctx.send('Player havent started any game :c')
                return
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
                                     color=yellow)
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
                                         color=yellow)
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
                    battlepoint += add_streak
                    await ctx.send(f'{player.name} win! Your Battle point: {battlepoint}')
                    if battlepoint >= 2147483647:
                        await ctx.send(f"{ctx.author.mention} Your battle point reached max\n"
                                       f"If you would like to reset you can do s!setpoint to any point you want "
                                       f"(below 2147483647)\n"
                                       f"Note: This command only usable if you have max point")
                        update_point(ctx.author.id, 2147483647)
                    else:
                        update_point(ctx.author.id, battlepoint)

                else:
                    await ctx.send(f'{enemy.name} win!')
                battleCooldown.pop(str(ctx.author.id))
                break
            log = system.process(rounds)

    @commands.command(name='teamgame', help='Have any idea making team?', aliases=["team"])
    async def teamgame(self, ctx, another_option=None, pos=None):
        team = game.find_one({"_id": f'team{ctx.author.id}'})
        if str(ctx.author.id) in owoCooldown:
            return
        rand_number = random.randint(0, 16777215)
        maxstat = 200
        team_hp, team_attack, team_speed, team_defense, team_ranges = [x for x in repeat(0, 5)]
        if game.count_documents({"_id": f'team{ctx.author.id}'}) != 0:
            if another_option in ["rr", "reroll"]:
                if pos.isdigit():
                    if int(pos) in range(1, 4):
                        x = int(pos)
                        team['team'][x]['char'] = random.choice(char_list)
                        team['team'][x]['hp'] = random.randrange(30, 81)
                        team['team'][x]['attack'] = random.randrange(30, 51 + (
                                100 - team['team'][x]['hp']))
                        team['team'][x]['speed'] = random.randrange(1, 6)
                        team['team'][x]['defense'] = maxstat - \
                            team['team'][x]['hp'] - \
                            team['team'][x]['attack'] - \
                            team['team'][x]['speed']
                        team['team'][x]['weapon'] = random.choice(list_weapon)
                        weapon = team['team'][x]['weapon']
                        team['team'][x]['attack1'] = weaponry[weapon]['attack']
                        team['team'][x]['speed1'] = weaponry[weapon]['speed']
                        team['team'][x]['ranges'] = weaponry[weapon]['range']
                        team['team'][x]['defense1'] = weaponry[weapon]['defense']
                        team['team'][x]['passive'] = weaponry[weapon]['passive']
                    else:
                        await ctx.send('Please input valid position to reroll', delete_after=5)
                        return
                else:
                    await ctx.send('Position must be number 1-3', delete_after=5)
                    return
            game.update_one({"_id": f'team{ctx.author.id}'}, {"$set": {"team": team['team']}})
            for x in range(1, 4):
                team_hp = team_hp + team['team'][x]['hp']
                team_attack = team_attack + team['team'][x]['attack'] + \
                    team['team'][x]['attack1']
                team_defense = team_defense + team['team'][x]['defense'] + \
                    team['team'][x]['defense1']
                team_speed = team_speed + team['team'][x]['speed'] + \
                    team['team'][x]['speed1']
                team_ranges = team_ranges + team['team'][x]['ranges']
        else:
            team = [None, {}, {}, {}]
            for x in range(1, 4):
                team[x] = {}
                team[x]['char'] = random.choice(char_list)
                team[x]['hp'] = random.randrange(30, 81)
                team[x]['attack'] = random.randrange(30, 51 + (
                        100 - team[x]['hp']))
                team[x]['speed'] = random.randrange(1, 6)
                team[x]['defense'] = maxstat - team[x]['hp'] - \
                    team[x]['attack'] - team[x]['speed']
                team[x]['weapon'] = random.choice(list_weapon)
                weapon = team[x]['weapon']
                team[x]['attack1'] = weaponry[weapon]['attack']
                team[x]['speed1'] = weaponry[weapon]['speed']
                team[x]['ranges'] = weaponry[weapon]['range']
                team[x]['defense1'] = weaponry[weapon]['defense']
                team[x]['passive'] = weaponry[weapon]['passive']
                team_hp = team_hp + team[x]['hp']
                team_attack = team_attack + team[x]['attack'] + \
                    team[x]['attack1']
                team_defense = team_defense + team[x]['defense'] + \
                    team[x]['defense1']
                team_speed = team_speed + team[x]['speed'] + \
                    team[x]['speed1']
                team_ranges = team_ranges + team[x]['ranges']
            game.insert_one({"_id": f'team{ctx.author.id}', "team": team})
        team_ranges = round(team_ranges / 3)
        team_speed = round(team_speed / 3)
        team_embed = discord.Embed(title=f'{ctx.author.name}\'s Team',
                                   description=f'Hp: {team_hp}  Attac: {team_attack}  Difens: {team_defense}'
                                               f'  Spid: {team_speed}'
                                               f'  Range: {team_ranges}',
                                   color=rand_number)
        team = game.find_one({"_id": f'team{ctx.author.id}'})
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
        team_embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=team_embed)
        owoCooldown.update({str(ctx.author.id): True})
        await asyncio.sleep(3)
        owoCooldown.pop(str(ctx.author.id))

    @commands.command(name='bossraid', help='Raid some boss with your team and show your skill!', aliases=['raidboss'])
    async def raid(self, ctx, difficulty):
        if str(ctx.author.id) in teamCooldown:
            return
        if game.count_documents({"_id": f'team{ctx.author.id}'}) == 0:
            await ctx.send('You dont have team :c')
            return
        if difficulty == 'e':
            stat = 10
        elif difficulty == 'h':
            stat = 20
        elif difficulty == 'i':
            stat = 30
        else:
            await ctx.send('Select difficulty e,h or i', delete_after=5)
            return
        rand_number = random.randint(0, 16777215)
        team = Team(ctx.author.id, f"{ctx.author.name}'s Team")
        boss = generate_enemy(stat, random.choice(random_name), 3 + random.randint(0, 35) / 100)
        system = Battle(team, boss)
        log = 'Battle started'
        raid = discord.Embed(title='Raid Boss', description=f'Round 0', color=rand_number)
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
            raid = discord.Embed(title='Raid Boss', description=f'Round {rounds} battle', color=rand_number)
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
                    await ctx.send(f'Your team won! <a:kittyhyper:742702283287953409>')
                else:
                    await ctx.send('Your team lost <a:crii:799610834769674252>')
                teamCooldown.pop(str(ctx.author.id))
                break
            log = system.process(rounds)

    @commands.command(name='teambattle', help='Wishing to battle with your friend team?')
    async def battlesystem(self, ctx, users: discord.User = None):
        if not users:
            await ctx.reply('who you wanna battle with? (userid works instead mention)', mention_author=False,
                            delete_after=5)
            return
        if str(ctx.author.id) in teamCooldown:
            return
        if game.count_documents({"_id": f'team{ctx.author.id}'}) == 0:
            await ctx.send("You dont have team :c")
            return
        if game.count_documents({"_id": f'team{users.id}'}) == 0:
            await ctx.send("User doesnt have team :c")
            return
        rand_number = random.randint(0, 16777215)
        team = Team(ctx.author.id, f"{ctx.author.name}'s team")
        enemy = Team(users.id, f"{users.name}'s team")
        system = Battle(team, enemy)

        log = 'Battle started'
        raid = discord.Embed(title='Raid enemy', description=f'Round 0', color=rand_number)
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

        # lets begin our date
        while True:
            raid = discord.Embed(title='Raid enemy', description=f'Round {rounds} battle', color=rand_number)
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

    @commands.command(name='wdesc', help='Description about weapon in game')
    async def desc(self, ctx, name=None):
        if not name:
            weapons = " | ".join(list_weapon)
            custom_embed = discord.Embed(title="Weapon List", description=weapons)
            custom_embed.set_footer(text="For specific weapon description, the name is the same as emoji name")
            await ctx.send(embed=custom_embed)
            return
        name = f':{name}:'
        rand_number = random.randint(0, 16777215)
        if name not in weaponry:
            await ctx.send('Input weapon name when', delete_after=5)
            return
        attack = weaponry[name]['attack']
        speed = weaponry[name]['speed']
        ranges = weaponry[name]['range']
        defense = weaponry[name]['defense']
        passive = weaponry[name]['passive']
        description = weaponry[name]['description']
        dexed = discord.Embed(title=name, description=f'Attac: {attack}\n'
                                                      f'Difens: {defense}\n'
                                                      f'Range: {ranges}\n'
                                                      f'Spid: {speed}\n'
                                                      f'Passife: {passive}\n'
                                                      f'{description}', color=rand_number)
        await ctx.send(embed=dexed)

    @commands.command(name='gameguide', help='Get started', aliases=['guidegame', 'startguide', 'guidestart'])
    async def guide(self, ctx):
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
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Game(bot))
