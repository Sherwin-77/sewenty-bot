from dataclasses import dataclass
import random
from typing import List, TYPE_CHECKING


if TYPE_CHECKING:
    from .hero import Hero


@dataclass
class State:
    """
    Represent battle state:

    0: Setup

    1: Pre attack

    2: During attack

    3: Counterattack

    4: Post attack
    """
    state_at: int
    buffs: List
    debuffs: List
    distance: int
    rounds: int


class Battle:
    def __init__(self, allies: Hero, enemy: Hero):
        self.allies = allies
        self.enemy = enemy
        self.distance = allies.ranges + enemy.ranges + allies.speed + enemy.speed

    def start(self):
        log = ""
        for weapon in ([self.allies.weapon] if isinstance(self.allies.weapon, str) else self.allies.weapon):
            if weapon == ":door:":
                self.allies.defense += round(self.allies.defense * 0.85)
                log += f"\n{self.allies.name} using :shield: buffing defense by 85%"
            elif weapon == ":broom:":
                self.allies.attack += round(self.enemy.attack * 0.30)
                self.allies.defense += round(self.enemy.defense * 0.30)
                log += f"\n{self.allies.name} using :trident: buffing itself by 30% " \
                       f"{self.enemy.name} attack and defense"
            elif weapon == ":game_die:":
                rolled_number = random.randint(1, 6)
                self.allies.attack += round(self.allies.attack * 0.085 * rolled_number)
                self.allies.hp += round(self.allies.hp * 0.085 * rolled_number)
                self.allies.defense += round(self.allies.defense * 0.085 * rolled_number)
                log = log + f"\n{self.allies.name} rolled dice and get **{rolled_number}**. " \
                            f"Increase stat by {rolled_number * 8.5}%"
            elif weapon == ":pick:":
                self.enemy.defense -= round(self.enemy.defense * 0.7)
                self.allies.defense -= round(self.allies.defense * 0.1)
                log += f"\n{self.allies.name} using :tools: decreasing {self.enemy.name} def by 70% and " \
                       f"{self.allies.name} defense by 10%"

        for weapon in ([self.enemy.weapon] if isinstance(self.enemy.weapon, str) else self.enemy.weapon):
            if weapon == ":door:":
                self.enemy.defense += round(self.enemy.defense * 0.85)
                log += f"\n{self.enemy.name} using :shield: buffing defense by 85%"
            elif weapon == ":broom:":
                self.enemy.attack += round(self.allies.attack * 0.30)
                self.enemy.defense += round(self.allies.defense * 0.30)
                log += f"\n{self.enemy.name} using :trident: buffing itself by 30% " \
                       f"{self.allies.name} attack and defense"
            elif weapon == ":game_die:":
                rolled_number = random.randint(1, 6)
                self.enemy.attack += round(self.enemy.attack * 0.085 * rolled_number)
                self.enemy.hp += round(self.enemy.hp * 0.085 * rolled_number)
                self.enemy.defense += round(self.enemy.defense * 0.085 * rolled_number)
                log += f"\n{self.enemy.name} rolled dice and get **{rolled_number}**. " \
                       f"Increase stat by {rolled_number * 8.5}%"
            elif weapon == ":pick:":
                self.allies.defense -= round(self.allies.defense * 0.7)
                self.enemy.defense -= round(self.enemy.defense * 0.1)
                log += f"\n{self.enemy.name} using :tools: decreasing {self.allies.name} def by 70% and " \
                       f"{self.enemy.name} defense by 10%"

        return log.strip() if log else "No early active weapon"

    def process(self, rounds):
        log = ""

        # bomb
        if ":bomb:" in self.allies.weapon and rounds % 5 == 1:
            self.enemy.hp -= round(self.allies.attack * 0.8)
            self.enemy.defense -= round(self.enemy.defense * 0.1)
            log = f"{self.allies.name} explode bomb and deal {round(self.allies.attack * 0.8)} damage to " \
                  f"{self.enemy.name} and decrease def by 10%"
        if ":bomb:" in self.enemy.weapon and rounds % 6 == 1:
            self.allies.hp -= round(self.enemy.attack * 0.8)
            self.allies.defense -= round(self.allies.defense * 0.1)
            log = f"\n{self.enemy.name} explode bomb and deal {round(self.enemy.attack * 0.8)} damage to " \
                  f"{self.enemy.name} and decrease def by 10%"

        # trigger broom
        if ":broom:" in self.allies.weapon and self.allies.chance(0.2):
            self.allies.attack += round(self.enemy.attack * 0.30)
            self.allies.defense += round(self.enemy.defense * 0.30)
            log += f"\n{self.allies.name} using :trident: buffing itself by 30% " \
                   f"{self.enemy.name} attack and defense"

        if ":broom:" in self.enemy.weapon and self.enemy.chance(0.2):
            self.enemy.attack += round(self.allies.attack * 0.30)
            self.enemy.defense += round(self.allies.defense * 0.30)
            log += f"\n{self.enemy.name} using :trident: buffing itself by 30% " \
                   f"{self.allies.name} attack and defense"

        # loudspeaker
        if ":loudspeaker:" in self.allies.weapon and self.allies.hp < self.enemy.hp:
            self.allies.attack += round(self.allies.attack * 0.18)
        if ":loudspeaker:" in self.enemy.weapon and self.enemy.hp < self.enemy.hp:
            self.enemy.attack += round(self.enemy.attack * 0.18)

        # door
        if ":door:" in self.allies.weapon and self.allies.hp < self.enemy.hp:
            self.allies.defense += round(self.allies.defense * 0.06)
        if ":door:" in self.enemy.weapon and self.enemy.hp < self.enemy.hp:
            self.enemy.defense += round(self.enemy.defense * 0.06)

        # before start, we set the power/damage
        self.allies.set_power(self.enemy)
        self.enemy.set_power(self.allies)

        while self.distance > self.allies.ranges and self.distance > self.enemy.ranges:
            # both out of range, so we move position of both side by their speed
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
            if ":bow_and_arrow:" in self.allies.weapon:
                self.allies.power += round(self.allies.power * 0.5)
            log += f"\n{self.allies.attacks(self.enemy, rounds, self.distance)}"
            self.distance = self.distance - self.enemy.speed

        else:
            # enemy is ranged mode while allies is chasing
            self.allies.is_ranged = False
            self.enemy.is_ranged = True
            if ":bow_and_arrow:" in self.enemy.weapon:
                self.enemy.power += round(self.enemy.power * 0.5)
            log += f"\n{self.enemy.attacks(self.allies, rounds, self.distance)}"
            self.distance = self.distance - self.allies.speed

        # compensation for ranged
        if self.distance + self.enemy.speed <= self.enemy.speed:
            self.distance = self.distance + round(self.enemy.speed / 4)
        elif self.distance + self.allies.speed <= self.allies.ranges:
            self.distance = self.distance + round(self.allies.speed / 4)

        return log.strip()
