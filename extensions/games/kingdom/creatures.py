from __future__ import annotations
import math

# Change below with anything you want
RENDERED_CREATURES = {
    "warrior": ["<a:reee1:975949205690531840>", "<a:reee:787642680007589918>"],
    "tank": ["<a:blossomradish:812889706249453618>", "<a:radishblossom:802357456885383198>"]
}


class BaseCreatures:
    def __init__(self, hp: int, defense: int, atk: int, level: int):
        self.hp = hp * level
        self.defense = int(defense * level/2)
        self.atk = int(atk * level/2)
        self.power = 0

    def special_skill(self, target):
        pass

    def set_power(self, target: BaseCreatures):
        """
        Set power done outside of creatures if not because of skill

        Parameters
        ----------
        target : BaseCreatures

        Returns
        -------
        None
        """
        if not isinstance(target, BaseCreatures):
            raise TypeError("Unexpected enemy")
        self.power = round(self.atk * math.exp(-target.defense / (self.atk + target.defense * 0.5)))

    def attack(self, target: BaseCreatures):
        target.hp -= self.power
        logs = f"{self} attack line of {target}, dealing {self.power} damage\n"
        return logs


class Warrior(BaseCreatures):
    def __init__(self, hp, defense, atk, level):
        super().__init__(hp, defense, int(atk * 1.2), level)

    def special_skill(self, target):
        pass

    def __str__(self):
        return "warrior"


class Tank(BaseCreatures):
    def __init__(self, hp, defense, atk, level):
        super().__init__(hp, int(defense * 1.2), atk, level)

    def special_skill(self, target):
        pass

    def __str__(self):
        return "tank"


CREATURES_ASSIGN = {
    "warrior": {
        "hp": 120,
        "def": 30,
        "atk": 50,
        "class": Warrior
    },
    "tank": {
        "hp": 150,
        "def": 35,
        "atk": 15,
        "class": Tank
    }
}


class Grouping:
    def attack(self, **options):
        pass

    def defend(self, enemy: dict, enemy_level: int):
        raise NotImplementedError
