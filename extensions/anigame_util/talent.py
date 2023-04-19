from __future__ import annotations
from typing import TYPE_CHECKING

from math import floor

if TYPE_CHECKING:
    from .card import AnigameCard


class AnigameTalent:
    def __init__(self, card: AnigameCard, enemy: AnigameCard, talent: str, stat_type: str):
        self.card = card
        self.enemy = enemy
        self.talent = talent
        self.stat_type = stat_type

    def overload(self):
        # decrease = 9 + self.rarity.value
        if self.stat_type not in {"atk", "defense"}:
            raise ValueError("Invalid stat")
        if self.stat_type == "atk":
            self.card.atk_percentage += 0.66 + (0.11 * self.card.rarity.value)
        if self.stat_type == "defense":
            self.card.defense_percentage += 0.66 + (0.11 * self.card.rarity.value)

    def berserker(self):
        if self.stat_type not in {"atk", "defense"}:
            raise ValueError("Invalid stat")
        if self.stat_type == "atk":
            self.card.atk_percentage += (0.36 + (0.06 * self.card.rarity.value))/self.card.atk_percentage
        if self.stat_type == "defense":
            self.card.defense_percentage += (0.36 + (0.11 * self.card.rarity.value))/self.card.defense_percentage

    def breaker(self):
        if self.stat_type not in {"atk", "defense"}:
            raise ValueError("Invalid stat")
        if self.stat_type == "atk":
            self.enemy.atk -= floor(self.enemy.atk * (0.24 + 0.04 * self.card.rarity.value))
        if self.stat_type == "defense":
            self.enemy.defense -= floor(self.enemy.defense * (0.24 + 0.04 * self.card.rarity.value))

    def trick(self):
        if self.stat_type not in {"atk", "defense"}:
            raise ValueError("Invalid stat")
        if self.stat_type == "atk":
            difference = max(self.enemy.atk * self.enemy.atk_percentage - self.card.atk * self.card.atk_percentage, 0)
            self.card.atk += floor(difference * (0.72 + 0.12 * self.card.rarity.value))
            self.enemy.atk -= floor(difference * (0.72 + 0.12 * self.card.rarity.value))
        if self.stat_type == "defense":
            difference = max(self.enemy.defense * self.enemy.defense_percentage -
                             self.card.defense * self.card.defense_percentage, 0)
            self.card.defense += floor(difference * (0.72 + 0.12 * self.card.rarity.value))
            self.enemy.defense -= floor(difference * (0.72 + 0.12 * self.card.rarity.value))

    def call_talent(self):
        if self.talent == "overload":
            self.overload()
        if self.talent == "berserker":
            self.berserker()
        if self.talent == "breaker":
            self.breaker()
        if self.talent == "trick":
            self.trick()

    def __str__(self):
        return self.stat_type.capitalize() + ' ' + self.talent.capitalize()
