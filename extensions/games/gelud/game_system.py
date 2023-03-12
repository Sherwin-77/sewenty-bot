import random

weaponry = {":bow_and_arrow:": {"attack": 37, "speed": 6, "range": 26, "defense": 16,
                                "passive": ":dart:",
                                "description": "**Archery**: Deal 50% more damage in ranged mode"},
            ":dagger:": {"attack": 46, "speed": 20, "range": 1, "defense": 18,
                         "passive": ":dash:",
                         "description": "**Dodge**: Gain 130% of speed as dodge chance"},
            ":axe:": {"attack": 52, "speed": 2, "range": 2, "defense": 24,
                      "passive": ":drop_of_blood:",
                      "description": "**Lifestyle**: heal you 50% of damage"},
            ":pick:": {"attack": 32, "speed": 5, "range": 1, "defense": 54,
                       "passive": ":tools:",
                       "description": "**Baccstab**: Decreasing enemy def by 70% and your def by 10%"},
            ":magic_wand:": {"attack": 36, "speed": 4, "range": 10, "defense": 36,
                             "passive": ":radioactive:",
                             "description": "**Chemical**: Deal 9% of enemy\"s current HP "
                                            "and heal by the damage dealt"},
            ":broom:": {"attack": 35, "speed": 7, "range": 2, "defense": 41,
                        "passive": ":trident:",
                        "description": "**Theft**: Steal 30% of enemy defense and attack. additionally,"
                                       " 20% chance to trigger again"},
            ":door:": {"attack": 26, "speed": 2, "range": 4, "defense": 52,
                       "passive": ":shield:",
                       "description": "**Thicc door**: Increase 85% defense. If your hp below enemy,"
                                      "Increase def by 6%"},
            ":bomb:": {"attack": 50, "speed": 4, "range": 17, "defense": 14,
                       "passive": ":boom:",
                       "description": "**Eksplosion**: Deal 80% of your attack as True Damage to enemy "
                                      "and decrease def by 10% every 5 rounds"},
            ":game_die:": {"attack": 30, "speed": 5, "range": 1, "defense": 30,
                           "passive": "<:lucc:796732732113682442>",
                           "description": "**Lucc Dice**: Roll 6 sided dice and increase hp atk and def by "
                                          "8.5x of rolled dice"},
            ":gun:": {"attack": 30, "speed": 6, "range": 23, "defense": 16,
                      "passive": ":microscope:",
                      "description": "**Precision**: Increase 3% crit chance and 5% crit dmg based on round"},
            ":satellite:": {"attack": 33, "speed": 2, "range": 4, "defense": 45,
                            "passive": ":satellite_orbital:",
                            "description": "**Radar**: Decrease incoming attack by 45% for every odd round"},
            ":loudspeaker:": {"attack": 46, "speed": 4, "range": 1, "defense": 32,
                              "passive": ":beginner:",
                              "description": "**Motivesien**: While your hp is lower than enemy, increase atk by 18%"},
            ":firecracker:": {"attack": 68, "speed": 3, "range": 3, "defense": 10,
                              "passive": ":fireworks:",
                              "description": "**Fataliti**: Every round, 30% chance to deal fatality "
                                             "(45% if your hp is below enemy), Sacrifice your 5% def and "
                                             "dealing 25-40% (40-55% if your hp below enemy)"
                                             " of your atk as well as "
                                             "decreasing enemy def by 25-40% of your atk "
                                             "(enemy def can\"t be lower than your def).\n"
                                             "If this fails, decrease your atk by 8% and increase def by 8%"},
            # ":school:": {"attack": 48, "speed": 2, "range": 3, "defense": 30,
            #              "passive": ":scales:",
            #              "description": "**Learn**: Every round, apply stun and permanently decrease def by 10% "
            #                             "and activate one of following:\n"
            #                             "1. Increase attack by 200%\n"
            #                             "2. Decrease def by 50%\n"
            #                             "3. Increase range by 100% and speed by 100%\n"
            #                             "4. Immune to next attack"}
            }


class Battle:
    def __init__(self, allies, enemy):
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
            # both out of range so we move position of both side by their speed
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
