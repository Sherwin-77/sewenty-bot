from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING
from .constants import ELEMENT, Rarity

if TYPE_CHECKING:
    from .talent import AnigameTalent


class AnigameCard:
    def __init__(
        self,
        base_atk: int,
        defense: int,
        element: List[str],
        crit_multiplier: float = 1.75,
        rarity: Rarity = Rarity.COMMON,
    ):
        self.base_atk = base_atk
        self.atk = base_atk
        self.base_defense = defense
        self.defense = defense
        self.element = [em if em in ELEMENT else "neutral" for em in element]
        self.crit_multiplier = crit_multiplier
        self.atk_percentage = 1.0
        self.defense_percentage = 1.0
        self.rarity = rarity
        self.talent: Optional[AnigameTalent] = None

    def element_multiplier(self, enemy_element: List[str]):
        total = 0
        for em in self.element:
            for op in enemy_element:
                if em == op and em != "neutral":
                    total -= 0.5
                elif ELEMENT[em] == op:
                    total += 1
                elif ELEMENT[op] == em:
                    total -= 1
        return 1 + (total / (len(self.element) * len(enemy_element))) * 0.5

    def damage(self, enemy: AnigameCard, crit: bool = False):
        ret = (
            (
                ((self.base_atk / (enemy.defense * enemy.defense_percentage)) * (self.atk * self.atk_percentage / 2.9))
                + 220000 / (enemy.defense * enemy.defense_percentage)
            )
            / 3
            * self.element_multiplier(enemy.element)
        )
        if crit:
            ret *= self.crit_multiplier
        return ret

    def reset(self):
        self.atk = self.base_atk
        self.defense = self.base_defense
        self.crit_multiplier = 1.75
        self.atk_percentage = 1
        self.defense_percentage = 1
        self.rarity = Rarity.COMMON
        self.talent = None
