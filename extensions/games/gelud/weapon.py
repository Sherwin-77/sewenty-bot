from __future__ import annotations

import random
from typing import TYPE_CHECKING, Optional, List

from enum import Enum


if TYPE_CHECKING:
    from .hero import Hero
    from .game_system import State


class Effect(Enum):
    DODGE = ":dash:"


class BaseWeapon:
    def check(self, **kwargs):
        raise NotImplementedError

    def attack(self, **kwargs):
        raise NotImplementedError


class HeroWeapon(BaseWeapon):
    def __init__(self, wielder: Hero):
        self.wielder = wielder
        self.passive = None

    def check(self, enemy: Hero, state: State, enemy_state: State) -> Optional[str]:
        raise NotImplementedError

    def attack(self, enemy: Hero, state: State, enemy_state: State) -> str:
        return self.wielder.default_attack(enemy, state, enemy_state)[0]

    def __eq__(self, other):
        return isinstance(self, type(other))

    def __hash__(self):
        return hash(self.__class__.__name__)

    def __str__(self):
        return "Weapon"


class TeamWeapon(HeroWeapon):
    def __init__(self, wielder: Hero, list_team_weapons: List[HeroWeapon]):
        super().__init__(wielder)
        self._list_weapon = list(set(list_team_weapons))

    def check(self, enemy: Hero, state: State, enemy_state: State) -> Optional[str]:
        log = ''
        for wp in self._list_weapon:
            wp: HeroWeapon
            s = wp.check(enemy, state, enemy_state)
            if s is not None:
                log += s + '\n'
        return log.strip()

    def attack(self, enemy: Hero, state: State, enemy_state: State) -> str:
        log = ''
        ori_power = self.wielder.power
        for wp in self._list_weapon:
            wp: HeroWeapon
            self.wielder.power = ori_power // len(self._list_weapon)
            log += wp.attack(enemy, state, enemy_state) + '\n'
        return log.strip()


# Weapon list here?
class Bow(HeroWeapon):
    """
    **Archery**: Deal 50% more damage in ranged mode
    """
    def __init__(self, wielder: Hero):
        super().__init__(wielder)
        self.passive = ":dart:"

    def check(self, enemy: Hero, state: State, enemy_state: State) -> Optional[str]:
        if state.state_at != 2:
            return
        if self.wielder.is_ranged:
            self.wielder.power += round(self.wielder.power * 0.5)
        self.wielder.ranges += 2

    def __str__(self):
        return ":bow_and_arrow:"


class Dagger(HeroWeapon):
    """
    **Dodge**: Gain 130% of speed as dodge chance
    """
    def __init__(self, wielder: Hero):
        super().__init__(wielder)
        self.passive = ":dash:"

    def check(self, enemy: Hero, state: State, enemy_state: State) -> Optional[str]:
        if state.state_at != 1:
            return

        if self.wielder.chance(self.wielder.speed * 0.0125):
            state.buffs.append(Effect.DODGE)
            return f"{self.wielder.name} stacked {Effect.DODGE.value} buff"
        else:
            self.wielder.speed += 1
            return f"{self.wielder.name} failed to stack {Effect.DODGE.value} buff. Increasing speed by 1"

    def __str__(self):
        return ":dagger:"


class Axe(HeroWeapon):
    """
    **Lifestyle**: heal you 50% of damage
    """
    def __init__(self, wielder: Hero):
        super().__init__(wielder)
        self.passive = ":drop_of_blood:"

    def check(self, enemy: Hero, state: State, enemy_state: State) -> Optional[str]:
        return

    def attack(self, enemy: Hero, state: State, enemy_state: State) -> str:
        log, success = self.wielder.default_attack(enemy, state, enemy_state)
        if not success:
            return log
        self.wielder.hp += round(self.wielder.power * 0.60)
        log += f"\n{self.passive}: {self.wielder.name} heal by **{round(self.wielder.power * 0.60)}** hp"
        return log

    def __str__(self):
        return ":axe:"


class Pickaxe(HeroWeapon):
    """
    **Baccstab**: Decreasing enemy def by 70% and your def by 10%
    """
    def __init__(self, wielder: Hero):
        super().__init__(wielder)
        self.passive = ":tools:"

    def check(self, enemy: Hero, state: State, enemy_state: State) -> Optional[str]:
        if state.state_at == 0 or (state.state_at == 1 and self.wielder.chance(0.005)):
            enemy.defense -= round(enemy.defense * 0.70)
            self.wielder.defense -= round(self.wielder.defense * 0.10)
            return (f"{self.wielder.name} using {self.passive}, decreasing {self.wielder.name} def by 70% and " 
                    f"{self.wielder.name} defense by 10%")

    def __str__(self):
        return ":pick:"


class MagicWand(HeroWeapon):
    """
    **Chemical**: Deal 9% of enemy's current HP and heal by the damage dealt
    """
    def __init__(self, wielder: Hero):
        super().__init__(wielder)
        self.passive = ":radioactive:"

    def check(self, enemy: Hero, state: State, enemy_state: State) -> Optional[str]:
        if state.state_at != 4:
            return
        damage = round(enemy.hp * 0.10) if self.wielder.hp > enemy.hp else round(enemy.hp * 0.08)
        heal = round(damage * 1.15) if self.wielder.hp < enemy.hp else damage
        self.wielder.hp += heal
        enemy.hp -= damage
        return f"{self.passive}: {self.wielder.name} deal **{damage}** damage to {enemy.name} and heal by **{heal}**"

    def __str__(self):
        return ":magic_wand:"


class Broom(HeroWeapon):
    """
    **Theft**: Steal 20% of enemy defense and attack. additionally, 20% chance to trigger again
    """
    def __init__(self, wielder: Hero):
        super().__init__(wielder)
        self.passive = ":trident:"

    def check(self, enemy: Hero, state: State, enemy_state: State) -> Optional[str]:
        if state.state_at == 0 or (state.state_at == 1 and self.wielder.chance(0.01)):
            self.wielder.attack += round(enemy.attack * 0.15)
            enemy.attack -= round(enemy.attack * 0.15)
            self.wielder.defense += round(enemy.defense * 0.15)
            enemy.defense -= round(enemy.defense * 0.15)
            return f"{self.wielder.name} using {self.passive}, stealing 15% of {enemy.name} attack and defense"

    def __str__(self):
        return ":broom:"


class Door(HeroWeapon):
    """
    **Thicc door**: Increase 85% defense. If your hp below enemy, Increase def by 6%
    """
    def __init__(self, wielder: Hero):
        super().__init__(wielder)
        self.passive = ":shield:"

    def check(self, enemy: Hero, state: State, enemy_state: State) -> Optional[str]:
        if state.state_at == 0:
            self.wielder.defense += round(self.wielder.defense * 0.65)
            return f"{self.wielder.name} using {self.passive} buffing defense by 65%"
        if state.state_at == 1 and self.wielder.hp < enemy.hp:
            self.wielder.defense += round(self.wielder.defense * 0.065)
            return f"{self.passive}: {self.wielder.name} increase defense by 6.5%"

    def __str__(self):
        return ":door:"


class Bomb(HeroWeapon):
    """
    **Eksplosion**: Deal 80% of your attack as True Damage to enemy and decrease def by 10% every 5 rounds
    """
    def __init__(self, wielder: Hero):
        super().__init__(wielder)
        self.passive = ":boom:"

    def check(self, enemy: Hero, state: State, enemy_state: State) -> Optional[str]:
        if state.state_at > 1 or state.rounds % 4 > 0:
            return

        enemy.hp -= round(self.wielder.attack * 0.8)
        enemy.defense -= round(enemy.defense * 0.1)
        return (f"{self.wielder.name} explode bomb and deal {round(self.wielder.attack * 0.8)} damage to " 
                f"{enemy.name} and decrease def by 10%")

    def __str__(self):
        return ":bomb:"


class Dice(HeroWeapon):
    """
    **Lucc Dice**: Roll 6 sided dice and increase hp atk and def by 8.5x of rolled dice
    """
    def __init__(self, wielder: Hero):
        super().__init__(wielder)
        self.passive = "<:lucc:796732732113682442>"

    def check(self, enemy: Hero, state: State, enemy_state: State) -> Optional[str]:
        if state.state_at == 0 or (state.state_at == 1 and self.wielder.chance(0.15)):
            rolled_number = random.randint(1, 20)
            self.wielder.attack += round(0.005 * rolled_number)
            self.wielder.hp += round(self.wielder.hp * 0.005 * rolled_number)
            self.wielder.defense += round(self.wielder.defense * 0.005 * rolled_number)
            return (f"{self.wielder.name} rolled dice and get **{rolled_number}**. "
                    f"Increase stat by {rolled_number * 5}%")

    def __str__(self):
        return ":game_die:"


class Gun(HeroWeapon):
    """
    **Precision**: Increase 3% crit chance and 5% crit dmg based on round
    """
    def __init__(self, wielder: Hero):
        super().__init__(wielder)
        self.passive = ":beginner:"

    def check(self, enemy: Hero, state: State, enemy_state: State) -> Optional[str]:
        if state.state_at != 2:
            return

        if self.wielder.chance(0.01 + 0.03 * state.rounds):
            self.wielder.power = round(self.wielder.power * (2 + 0.05 * state.rounds))
            return (f"{self.wielder.name} succesfully using {self.passive}. "
                    f"Increasing damage dealt by {(200 + 5 * state.rounds)}%")
        else:
            self.wielder.power = round(self.wielder.power * (0.69 - (0.01 * state.rounds)))
            return (f"{self.wielder.name} failed to use {self.passive}. "
                    f"Reducing damage dealt to {69 - (1 * state.rounds)}%")

    def __str__(self):
        return ":gun:"


class Satellite(HeroWeapon):
    """
    **Radar**: Decrease incoming attack by 45% for every odd round
    """
    def __init__(self, wielder: Hero):
        super().__init__(wielder)
        self.passive = ":satellite_orbital:"

    def check(self, enemy: Hero, state: State, enemy_state) -> Optional[str]:
        if state.state_at != 2:
            return

        log = ""
        if state.rounds % 2 == 0:
            enemy.power -= round(enemy.power * 0.45)
            log += f"{self.passive}: {self.wielder.name} reduce damage dealt of {enemy.name} by 45%\n"

        if self.wielder.chance(0.25):
            enemy.power -= round(enemy.power * 0.30)
            log += f"{self.wielder.name} using {self.passive}. Reducing damage dealt of {enemy.name} by 30%"

        return None if not log else log

    def __str__(self):
        return ":satellite:"


class Loudspeaker(HeroWeapon):
    """
    **Motivesien**: While your hp is lower than enemy, increase atk by 18%
    """
    def __init__(self, wielder: Hero):
        super().__init__(wielder)
        self.passive = ":beginner:"

    def check(self, enemy: Hero, state: State, enemy_state: State) -> Optional[str]:
        if state.state_at != 1:
            return

        if self.wielder.hp < enemy.hp:
            self.wielder.attack += round(self.wielder.attack * 0.20)
            return f"{self.passive}: {self.wielder.name} increase attack by 20%"

    def __str__(self):
        return ":loudspeaker:"


class Firecracker(HeroWeapon):
    """
    **Fataliti**: Every round, 30% chance to deal fatality (45% if your hp is below enemy),

    Sacrifice your 5% def and dealing 25-40% (40-55% if your hp below enemy) of your atk as well as
    decreasing enemy def by 25-40% of your atk (enemy def can't be lower than your def).


    If this fails, decrease your atk by 8% and increase def by 8%
    """
    def __init__(self, wielder: Hero):
        super().__init__(wielder)
        self.passive = ":fireworks:"

    def check(self, enemy: Hero, state: State, enemy_state: State) -> Optional[str]:
        if state.state_at > 1:
            return
        if self.wielder.chance(0.3 + (0.15 if self.wielder.hp < enemy.hp else 0)):
            delimiter = random.randint(0, 15) / 100
            damage_bound = 0.55 if self.wielder.hp <= enemy.hp else 0.4
            self.wielder.defense -= round(self.wielder.defense * 0.05)
            enemy.hp -= round((damage_bound - delimiter) * self.wielder.attack)
            if self.wielder.defense < enemy.defense:
                enemy.defense -= round((0.4 - delimiter) * self.wielder.attack)

            return (f"{self.wielder.name} deals **fatality** dmg, " 
                    f"dealing **{round((damage_bound - delimiter) * self.wielder.attack)}** " 
                    f"dmg as well as decreasing {enemy.name} def by " 
                    f"{round((0.4 - delimiter) * 100)}% of {self.wielder.name}'s atk\n")
        else:
            self.wielder.attack -= round(0.08 * self.wielder.attack)
            self.wielder.defense += round(0.08 * self.wielder.defense)
            return f"{self.wielder.name} fails to deal fatality"

    def __str__(self):
        return ":firecracker:"
