from __future__ import annotations

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
        self.allies_buffs = []
        self.allies_debuffs = []
        self.enemy_buffs = []
        self.enemy_debuffs = []
        self.rounds = -1
        self.battle_at = 0

    @property
    def allies_state(self):
        return State(self.battle_at, self.allies_buffs, self.allies_debuffs, self.distance, self.rounds)

    @property
    def enemy_state(self):
        return State(self.battle_at, self.enemy_buffs, self.enemy_debuffs, self.distance, self.rounds)

    def _check(self) -> str:
        log = ""
        s = self.allies.check(self.enemy, self.allies_state, self.enemy_state)
        if s is not None:
            log += s + '\n'
        s = self.enemy.check(self.allies, self.allies_state, self.enemy_state)
        if s is not None:
            log += s + '\n'

        return log

    def run(self):
        log = ""
        reduce_dist = 0

        if self.rounds == -1:
            log += self._check()
            if not log:
                log = "No passive used this round :)"
        else:
            for x in range(1, 5):
                self.battle_at = x

                if self.battle_at == 2:
                    a = self.allies
                    b = self.enemy

                    self.allies.set_power(a)
                    self.enemy.set_power(b)

                    while self.distance > a.ranges and self.distance > b.ranges:
                        self.distance = max(0, self.distance-a.speed-b.speed)
                    if a.ranges >= self.distance > self.enemy.ranges:
                        a.is_ranged = True
                        b.is_ranged = False
                        reduce_dist = b.speed
                    elif self.allies.ranges < self.distance <= self.enemy.ranges:
                        a.is_ranged = False
                        b.is_ranged = True
                        reduce_dist = a.speed
                    else:
                        a.is_ranged = b.is_ranged = False

                    log += self._check()
                    log += "===== **ATTACK PHASE** =====\n"
                    log += f"| __At distance **{self.distance}** Hyper meter__ |\n"
                    c = self.allies_state
                    d = self.enemy_state
                    if a.speed < b.speed:
                        a, b = b, a
                        c, d = d, c

                    if any([a.is_ranged, b.is_ranged]):
                        if not a.is_ranged:
                            log += b.attacks(a, d, c) + '\n'
                        else:
                            log += a.attacks(b, c, d) + '\n'
                    else:
                        log += a.attacks(b, c, d) + '\n'
                        log += b.attacks(a, d, c) + '\n'

                    log += "===========================\n"
                else:
                    log += self._check()

        if self.distance < self.allies.ranges:
            self.distance = min(self.allies.ranges, self.distance + self.allies.speed//2)
        if self.distance < self.enemy.ranges:
            self.distance = min(self.enemy.ranges, self.distance + self.enemy.speed//2)

        self.distance = max(0, self.distance
                            - round((reduce_dist
                                     * (1+abs(self.allies.hp-self.enemy.hp)/(self.allies.hp + self.enemy.hp)))))
        self.rounds += 1

        return log.strip()
