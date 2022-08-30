from collections import deque
from typing import Dict

from .creatures import RENDERED_CREATURES, CREATURES_ASSIGN, BaseCreatures


class Battle:
    def __init__(self, ally: Dict[str, int], enemy: Dict[str, int], ally_level: int, enemy_level: int):
        self.ally = ally
        self.enemy = enemy

        self.ally_rendered = [RENDERED_CREATURES.get(a, [a, a])[0] for a in self.ally.keys()]
        self.enemy_rendered = [RENDERED_CREATURES.get(e, [e, e])[1] for e in self.enemy.keys()]

        self.ally_formation = deque(maxlen=len(CREATURES_ASSIGN.keys()))
        self.enemy_formation = deque(maxlen=len(CREATURES_ASSIGN.keys()))

        for k, v in self.ally.items():
            if k not in CREATURES_ASSIGN:
                raise ValueError("Invalid creatures")
            blueprint = CREATURES_ASSIGN[k]["class"]
            ally: BaseCreatures = blueprint(hp=CREATURES_ASSIGN[k]["hp"] * v,
                                            defense=CREATURES_ASSIGN[k]["def"] * v,
                                            atk=CREATURES_ASSIGN[k]["atk"] * v,
                                            level=ally_level)
            self.ally_formation.append(ally)

        for k, v in self.enemy.items():
            if k not in CREATURES_ASSIGN:
                raise ValueError("Invalid creatures")
            blueprint = CREATURES_ASSIGN[k]["class"]
            enemy: BaseCreatures = blueprint(hp=CREATURES_ASSIGN[k]["hp"] * v,
                                             defense=CREATURES_ASSIGN[k]["def"] * v,
                                             atk=CREATURES_ASSIGN[k]["atk"] * v,
                                             level=enemy_level)
            self.enemy_formation.append(enemy)

    def show(self) -> str:
        return ' '.join(self.ally_rendered[::-1]) + ' ⚔ ' + ' '.join(self.enemy_rendered)

    def complex_show(self) -> (str, str):
        return ('\n'.join(f"{str(ally).capitalize()}\n"
                          f"Hp: {ally.hp}\n"
                          f"Def: {ally.defense}\n"
                          f"Atk: {ally.atk}" for ally in self.ally_formation),
                '\n'.join(f"{str(enemy).capitalize()}\n"
                          f"Hp: {enemy.hp}\n"
                          f"Def: {enemy.defense}\n"
                          f"Atk: {enemy.atk}" for enemy in self.enemy_formation))

    @property
    def is_done(self) -> bool:
        return len(self.enemy_formation) <= 0 or len(self.ally_formation) <= 0

    def get_remaining(self):
        self.ally = {}
        self.enemy = {}
        if len(self.ally_formation) > 0:
            for ally in self.ally_formation:
                counts = (ally.hp // 2 // CREATURES_ASSIGN[str(ally)]["hp"]) or 1
                self.ally.update({str(ally): counts})
        if len(self.enemy_formation) > 0:
            for enemy in self.enemy_formation:
                counts = (enemy.hp // 2 // CREATURES_ASSIGN[str(enemy)]["hp"]) or 1
                self.enemy.update({str(enemy): counts})
        return self.ally, self.enemy

    def next_turn(self):
        # FIXME: Fix logic for turn based battle
        logs = ""
        ally_line = 0
        enemy_line = 0
        while ally_line < len(self.ally_formation) and enemy_line < len(self.enemy_formation):
            if len(self.ally_formation) > ally_line:
                ally: BaseCreatures = self.ally_formation[ally_line]
                ally.set_power(self.enemy_formation[0])
                logs += "**Allies turn**\n"
                logs += ally.attack(self.enemy_formation[0])
                ally_line += 1
                if self.enemy_formation[0].hp <= 0:
                    logs += "Enemies front line destroyed!\n"
                    self.enemy_formation.popleft()
                    if enemy_line > 0:
                        enemy_line -= 1

            if len(self.enemy_formation) <= enemy_line:
                continue

            enemy = self.enemy_formation[enemy_line]
            enemy: BaseCreatures
            enemy.set_power(self.ally_formation[0])
            logs += "**Enemies turn**\n"
            logs += enemy.attack(self.ally_formation[0])
            if self.ally_formation[0].hp <= 0:
                logs += "Allies front line destroyed!\n"
                self.ally_formation.popleft()
                if ally_line > 0:
                    ally_line -= 1
            enemy_line = (enemy_line + 1) % len(self.enemy_formation)
        if len(self.enemy_formation) <= 0:
            logs += "Allies win\n"
        if len(self.ally_formation) <= 0:
            logs += "Enemies win\n"

        return logs.strip()
