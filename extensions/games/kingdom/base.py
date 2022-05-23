from .battlefield import Battle
from .creatures import Grouping

import datetime
from typing import Optional, Dict


class TooQuickCollect(ValueError):
    pass


class NotEnoughGold(ValueError):
    pass


class Base(Grouping):
    SOLDIER_TYPES = ["warrior", "tank"]

    def __init__(self,
                 soldier: Optional[Dict[str, int]] = None,
                 level: int = 1,
                 gold: int = 1000,
                 last_collect: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)):
        if soldier is None:
            # give new player starter soldier
            soldier = {"tank": 10,
                       "warrior": 10}
        self._soldiers = soldier
        self.level = level
        self.gold = gold
        self.last_collect = last_collect

    @property
    def soldiers(self) -> Optional[Dict[str, int]]:
        return self._soldiers.copy()

    @property
    def training_cost(self) -> int:
        return 10 * self.level ** 2

    @property
    def upgrade_cost(self) -> int:
        return 100 * self.level ** 3

    def train(self, soldier_type: Dict[str, int]):
        total_soldier = 0
        for v in soldier_type.values():
            if not isinstance(v, int):
                raise TypeError("Value must be int")
            total_soldier += v
        if self.training_cost * total_soldier > self.gold:
            raise NotEnoughGold("You don't have enough gold to perform training")
        for key, value in soldier_type.items():
            if key not in self.SOLDIER_TYPES:
                raise ValueError("Invalid soldier type")
            if key not in self._soldiers.keys():
                self._soldiers.update({key: value})
            else:
                self._soldiers[key] += value
        self.gold -= self.training_cost * total_soldier

    def upgrade(self):
        if self.upgrade_cost > self.gold:
            raise NotEnoughGold("You don't have enough gold to perform training")
        self.level += 1
        self.gold -= self.upgrade_cost

    def collect_golds(self, collect_date: datetime.datetime):
        total_seconds = abs((collect_date - self.last_collect).total_seconds())
        if total_seconds < 1:
            raise TooQuickCollect("You are collecting gold too quick")
        gain = int(total_seconds * 2 * self.level)
        self.last_collect = collect_date
        self.gold += gain
        return gain

    def attack(self, enemy: Grouping, soldier_sent: Dict[str, int]):
        for key, value in soldier_sent.items():
            if key not in self.SOLDIER_TYPES:
                raise ValueError("Invalid soldier type")
            if not isinstance(value, int):
                raise TypeError("Value must be int")
            if key not in self._soldiers.keys() or self._soldiers[key] < value:
                raise ValueError("Soldier not found or not enough soldier to sent")
            self._soldiers[key] -= value
        return enemy.defend(soldier_sent, self.level)

    def returned(self, soldier_returned: Dict[str, int]):
        for key, value in soldier_returned.items():
            if key not in self.SOLDIER_TYPES:
                raise ValueError("Invalid soldier type")
            if not isinstance(value, int):
                raise TypeError("Value must be int")
            if key not in self._soldiers:
                self._soldiers.update({key: value})
            else:
                self._soldiers[key] += value

    def update_soldier(self, new_soldier: Dict[str, int]):
        self._soldiers = new_soldier

    def defend(self, enemy: Dict[str, int], enemy_level: int):
        return Battle(enemy, self.soldiers, ally_level=self.level, enemy_level=enemy_level)
