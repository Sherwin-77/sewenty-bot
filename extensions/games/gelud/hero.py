from __future__ import annotations

import random
import math
from typing import TYPE_CHECKING, Tuple, List, Union

from .items import WEAPONRY
from .weapon import Effect


if TYPE_CHECKING:
    from .game_system import State
    from .weapon import HeroWeapon


class Hero:
    _weapon: HeroWeapon

    def __init__(
        self,
        name: str,
        char: str,
        weapon: Union[str, HeroWeapon],
        hp: int,
        attack: int,
        speed: int,
        defense: int,
        ranges: int,
    ):
        self.name = name
        self.char = char
        if isinstance(weapon, str):
            self._weapon = WEAPONRY[weapon]["weapon"](self)
        else:
            self._weapon = weapon
        self.hp = hp
        self.attack = attack
        self.speed = speed
        self.defense = defense
        self.ranges = ranges
        self.power = 0
        self.is_ranged = False

    @property
    def weapon(self):
        return self._weapon.__str__()

    def check(self, enemy: Hero, state: State, enemy_state: State):
        return self._weapon.check(enemy, state, enemy_state)

    @staticmethod
    def _get_effect(effect: Effect, arr: List):
        try:
            arr.remove(effect)
        except ValueError:
            return None
        else:
            return effect

    def set_power(self, target: Hero):
        if not isinstance(target, Hero):
            raise TypeError("Unexpected Type to attack")
        self.power = round(self.attack * math.exp(-target.defense / (self.attack + target.defense * 0.5)))

    def default_attack(self, target: Hero, state: State, target_state: State) -> Tuple[str, bool]:
        if not isinstance(target, Hero):
            raise TypeError("Unexpected Type to attack")

        critical = False
        if self.chance(0.05):
            self.power *= 2
            critical = True

        if target.chance(0.01):
            return f"{target.name} managed to **dodge** {self.name}'s attack and take no damage", False

        if self._get_effect(Effect.DODGE, target_state.buffs):
            return (
                f"**[BUFF]** {Effect.DODGE.value}: " f"{target.name} **dodge** {self.name}'s attack and take no damage",
                False,
            )

        target.hp -= self.power

        return (
            self.name
            + (f" have enough range at **{state.distance}** hyper meter and" if self.is_ranged else '')
            + f" deal **{self.power}** damage to {target.name}. "
            + ("**CRITICAL HIT**" if critical else ''),
            True,
        )

    def attacks(self, target: Hero, state: State, target_state: State) -> str:
        if not isinstance(target, Hero):
            raise TypeError("Unexpected Type to attack")

        return self._weapon.attack(target, state, target_state)

        # # critical and precision
        # critical = False
        # if ":gun:" in self.weapon:
        #     if self.chance(0.01 + 0.03 * rounds):
        #         self.power = round(self.power * (2 + 0.05 * rounds))
        #         critical = True
        # else:
        #     if self.chance(0.01):
        #         self.power *= 2
        #         critical = True
        #
        # # endurance
        # if ":satellite:" in target.weapon and rounds % 2 == 1:
        #     self.power -= round(self.power * 0.45)
        #
        # # fatality
        # if ":firecracker:" in self.weapon:
        #     if self.chance(0.3 + (0.15 if self.hp < target.hp else 0)):
        #         delimiter = random.randint(0, 15) / 100
        #         damage_bound = 0.55 if self.hp <= target.hp else 0.4
        #         self.defense -= round(self.defense * 0.05)
        #         target.hp -= round((damage_bound - delimiter) * self.attack)
        #         target.defense -= round((0.4 - delimiter) * self.attack) if target.defense > self.defense else 0
        #         log += f"{self.name} deals **fatality** dmg, " \
        #                f"dealing **{round((damage_bound - delimiter) * self.attack)}** " \
        #                f"dmg as well as decreasing {target.name} def by " \
        #                f"{round((0.4 - delimiter) * 100)}% of your atk\n"
        #     else:
        #         self.attack -= round(0.08 * self.attack)
        #         self.defense += round(0.08 * self.defense)
        #         log += f"{self.name} fails to deal fatality\n"
        #
        # # evasion and core atk
        # if ":dagger:" in target.weapon and target.chance(target.speed * 0.013):
        #     log += f"{target.name} dodge attack and take no damage"
        # else:
        #     target.hp -= self.power
        #     log += (f"{self.name} have enough range at **{distance}** hyper meter and"
        #             if self.is_ranged else self.name) + f" deal **{self.power}** damage to {target.name}"
        #     if ":axe:" in self.weapon:
        #         self.hp += round(self.power * 0.50)
        #         log += f" and heal itself {round(self.power * 0.50)} hp"
        #     log += " **CRITICAL HIT**" if critical else ""
        #
        # # wand
        # if ":magic_wand:" in self.weapon and target.hp > 0:
        #     self.hp += round(target.hp * 0.09 / 2) if self.hp >= target.hp else round(target.hp * 0.09)
        #     target.hp -= round(target.hp * 0.09)
        #     log = f"{log}\n" \
        #           f"{self.name} deal damage 9% of {target.name} hp and heal itself"
        # return log.strip()

    @staticmethod
    def chance(set_chance: float):
        return random.random() <= set_chance
