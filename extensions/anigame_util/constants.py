from enum import Enum


ELEMENT = {
    "ground": "electric",
    "electric": "water",
    "water": "fire",
    "fire": "grass",
    "grass": "ground",
    "light": "dark",
    "dark": "light",
    "neutral": ""
}

RENDER_ELEMENT = {
    "ground": "⛰",
    "electric": "🌩️",
    "water": "💦",
    "fire": "🔥",
    "grass": "🍂",
    "light": "💡",
    "dark": "🌛",
    "neutral": "✨"
}


class Rarity(Enum):
    COMMON = 0
    UNCOMMON = 1
    RARE = 2
    SR = 3
    UR = 4
    L = 5


STR_TO_RARITY = {
    "common": Rarity.COMMON,
    "uncommon": Rarity.UNCOMMON,
    "rare": Rarity.RARE,
    "super rare": Rarity.SR,
    "ultra rare": Rarity.UR,
    "legendary": Rarity.L
}
