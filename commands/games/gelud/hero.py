import random
import math


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
                    if self.is_ranged else self.name) + f" deal **{self.power}** damage to {target.name}"
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