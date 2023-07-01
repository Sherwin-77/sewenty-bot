from .weapon import *

WEAPONRY = {":bow_and_arrow:": {"attack": 37, "speed": 6, "range": 26, "defense": 16,
                                "passive": ":dart:",
                                "description": Bow.__doc__,
                                "weapon": Bow},
            ":dagger:": {"attack": 46, "speed": 20, "range": 1, "defense": 18,
                         "passive": ":dash:",
                         "description": Dagger.__doc__,
                         "weapon": Dagger},
            ":axe:": {"attack": 52, "speed": 2, "range": 2, "defense": 24,
                      "passive": ":drop_of_blood:",
                      "description": Axe.__doc__,
                      "weapon": Axe},
            ":pick:": {"attack": 32, "speed": 5, "range": 1, "defense": 54,
                       "passive": ":tools:",
                       "description": Pickaxe.__doc__,
                       "weapon": Pickaxe},
            ":magic_wand:": {"attack": 36, "speed": 4, "range": 10, "defense": 36,
                             "passive": ":radioactive:",
                             "description": MagicWand.__doc__,
                             "weapon": MagicWand},
            ":broom:": {"attack": 35, "speed": 7, "range": 2, "defense": 41,
                        "passive": ":trident:",
                        "description": Broom.__doc__,
                        "weapon": Broom},
            ":door:": {"attack": 26, "speed": 2, "range": 4, "defense": 52,
                       "passive": ":shield:",
                       "description": Door.__doc__,
                       "weapon": Door},
            ":bomb:": {"attack": 50, "speed": 4, "range": 17, "defense": 14,
                       "passive": ":boom:",
                       "description": Bomb.__doc__,
                       "weapon": Door},
            ":game_die:": {"attack": 30, "speed": 5, "range": 1, "defense": 30,
                           "passive": "<:lucc:796732732113682442>",
                           "description": Dice.__doc__,
                           "weapon": Dice},
            ":gun:": {"attack": 30, "speed": 6, "range": 23, "defense": 16,
                      "passive": ":microscope:",
                      "description": Gun.__doc__,
                      "weapon": Gun},
            ":satellite:": {"attack": 33, "speed": 2, "range": 4, "defense": 45,
                            "passive": ":satellite_orbital:",
                            "description": Satellite.__doc__,
                            "weapon": Satellite},
            ":loudspeaker:": {"attack": 46, "speed": 4, "range": 1, "defense": 32,
                              "passive": ":beginner:",
                              "description": Loudspeaker.__doc__,
                              "weapon": Loudspeaker},
            ":firecracker:": {"attack": 68, "speed": 3, "range": 3, "defense": 10,
                              "passive": ":fireworks:",
                              "description": Firecracker.__doc__,
                              "weapon": Firecracker},
            ":school:": {"attack": 48, "speed": 2, "range": 3, "defense": 30,
                         "passive": ":scales:",
                         "description": "**Learn**: Every round, apply stun and permanently decrease def by 10% "
                                        "and activate one of following:\n"
                                        "1. Increase attack by 200%\n"
                                        "2. Decrease def by 50%\n"
                                        "3. Increase range by 100% and speed by 100%\n"
                                        "4. Immune to next attack"}
            }