from dataclasses import dataclass

# noinspection SpellCheckingInspection
USER_AGENTS = (
    "Mozilla/5.0 (Linux; Android 12; "
    "SM-S906N Build/QP1A.190711.020; wv) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Version/4.0 Chrome/80.0.3987.119 Mobile Safari/537.36",

    "Mozilla/5.0 (X11; CrOS x86_64 14588.123.0) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/101.0.4951.72 Safari/537.36",

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/102.0.0.0 Safari/537.36",

    "Mozilla/5.0 (Windows NT 10.0; WOW64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/45.0.2454.85 Safari/537.36",

    "Mozilla/5.0 (Windows NT 10.0) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/42.0.2311.135 Safari/537.36 Edge/12.10240"
)

# noinspection SpellCheckingInspection
CHAR_LIST = [':man_walking:', ':woman_walking:', ':person_running:', ':woman_running:', ':sloth:',
             ':cat2:', ':dog2:', ':unicorn:', ':snail:', '<:snale:770847330600484864>', ':t_rex:',
             '<:EB_nekocute:780408575784255538>', ':wolf:', "<:MoriOwO:832762779450081312>",
             '<a:kittyrawr:719122783828967455>', '<a:kittymad:720191651175333898>',
             '<:babycuddle:751985441653391440>', '<:blobsob:809721186966831105>', ':snake:']

# noinspection SpellCheckingInspection
CHARACTER_NAMES = ["Ghost slayer", "Death mire", "P", "Yejing", "Skull grim", "Barrel", "Dark eye", "Vino", "Dio",
                   "Mono", "Not slime", "Paul", "Fenrir"]

EMOJI_STATUS = {
    "online": "🟢",
    "idle": "🌙",
    "dnd": "🚫",
    "offline": "⚫"
}

# noinspection SpellCheckingInspection
# weapon : {cost : (min, max)}
OWO_WEAPONS = {
    "bow": {
        "cost": (120, 220),
        "stat1": (110.0, 160.0),
        "image": "https://cdn.discordapp.com/emojis/594613521367695364.png?v=1",
        "total_stat": 1
    },
    "sword": {
        "cost": (150, 250),
        "stat1": (35.0, 55.0),
        "image": "https://cdn.discordapp.com/emojis/594613521271095299.png?v=1",
        "total_stat": 1
    },
    "aegis": {
        "cost": (150, 250),
        "stat1": (30.0, 50.0),
        "image": "https://cdn.discordapp.com/emojis/594613521648713767.png?v=1",
        "total_stat": 1
    },
    "estaff": {
        "cost": (100, 200),
        "stat1": (35.0, 65.0),
        "image": "https://cdn.discordapp.com/emojis/594613521736663051.png?v=1",
        "total_stat": 1
    },
    "vstaff": {
        "cost": (100, 200),
        "stat1": (25.0, 45.0),
        "image": "https://cdn.discordapp.com/emojis/594613521371627561.png?v=1",
        "total_stat": 1
    },
    "hstaff": {
        "cost": (125, 200),
        "stat1": (100.0, 150.0),
        "image": "https://cdn.discordapp.com/emojis/594613521950441481.png?v=1",
        "total_stat": 1
    },
    "axe": {
        "cost": (120, 220),
        "stat1": (50.0, 80.0),
        "image": "https://cdn.discordapp.com/emojis/622681663289294850.png?v=1",
        "total_stat": 1
    },
    "rstaff": {
        "cost": (300, 400),
        "stat1": (50.0, 80.0),
        "image": "https://cdn.discordapp.com/emojis/622681759880052757.png?v=1",
        "total_stat": 1
    },
    "scepter": {
        "cost": (125, 200),
        "stat1": (40.0, 70.0),
        "image": "https://cdn.discordapp.com/emojis/622681759330598913.png?v=1",
        "total_stat": 1
    },
    "dagger": {
        "cost": (100, 200),
        "stat1": (70.0, 100.0),
        "stat2": (40.0, 65.0),
        "image": "https://cdn.discordapp.com/emojis/594613521543856128.png?v=1",
        "total_stat": 2
    },
    "scythe": {
        "cost": (100, 200),
        "stat1": (70.0, 100.0),
        "stat2": (30.0, 60.0),
        "image": "https://cdn.discordapp.com/emojis/622681759401639936.png?v=1",
        "total_stat": 2
    },
    "sstaff": {
        "cost": (125, 225),
        "stat1": (30.0, 50.0),
        "stat2": (20.0, 30.0),
        "image": "https://cdn.discordapp.com/emojis/594613521581473851.png?v=1",
        "total_stat": 2
    },
    "wand": {
        "cost": (150, 250),
        "stat1": (80.0, 100.0),
        "stat2": (20.0, 40.0),
        "image": "https://cdn.discordapp.com/emojis/594613521703108631.png?v=1",
        "total_stat": 2
    },
    "banner": {
        "cost": (250, 300),
        "stat1": (10.0, 20.0),
        "stat2": (20.0, 30.0),
        "stat3": (30.0, 40.0),
        "image": "https://cdn.discordapp.com/emojis/622681759565479956.png?v=1",
        "total_stat": 3
    },
    "fstaff": {
        "cost": (100, 200),
        "stat1": (100.0, 200.0),
        "stat2": (20.0, 40.0),
        "stat3": (40.0, 60.0),
        "image": "https://cdn.discordapp.com/emojis/594613521573216266.png?v=1",
        "total_stat": 3
    }
}


@dataclass
class Colour:
    YELLOW = 0xffd700
    RED = 0x8b0000
    GRAY = 0x808080
    BLUE = 0x0000ff
    PURPLE = 0x800080
    CYAN = 0x00ffff
    ORANGE = 0xff8c00
