from __future__ import annotations

import discord
from discord.ext import commands

import asyncio
from math import floor
import random
import time
from typing import TYPE_CHECKING, List, Optional

from constants import OWO_WEAPONS, Colour
from extensions.anigame_util import AnigameCard, RENDER_ELEMENT, AnigameTalent, STR_TO_RARITY
from utils.view_util import BaseView, Dropdown

if TYPE_CHECKING:
    from main import SewentyBot


def max_weapon_stat(weapon_type: str, cost: int, stat1: float, stat2: float, stat3: float, stat4: float) -> discord.Embed:
    certified_detail = [
        [100, ("Fabled", Colour.CYAN, "<a:Fabled:760029464292884503>")],
        [95, ("Legendary", Colour.YELLOW, "<a:Legendary:760029450913316874>")],
        [81, ("Mythic", Colour.PURPLE, "<:mythic:760029618732007424>")],
        [61, ("Epic", Colour.BLUE, "<:epic:760029607755513886>")],
        [41, ("Rare", Colour.ORANGE, "<:rare:760029595365539850>")],
        [21, ("Uncommon", Colour.GRAY, "<:uncommon:760029577635692545>")],
        [0, ("Common", Colour.RED, "<:common:760029564649865267>")],
    ]

    custom_embed = discord.Embed(title="Stat", description=f"Type: {weapon_type.title()}", color=discord.Colour.random())

    if weapon_type is None or weapon_type.lower() not in OWO_WEAPONS:
        custom_embed.add_field(name="Invalid weapon type", value="Please input correct weapon type or use auto detect")
        return custom_embed

    selected_weapon = OWO_WEAPONS[weapon_type.lower()]
    total_stat = selected_weapon.get("total_stat", 1)
    image_url = selected_weapon.get("image")

    base_stat = 0

    rarity = "Below common"
    colour = None
    emoji = "<:blobsobOwO:843962665549692938>"

    if cost is None or cost < selected_weapon["cost"][0] or cost > selected_weapon["cost"][1]:
        custom_embed.add_field(
            name="Invalid weapon cost", value="Please input correct weapon cost or use auto detect", inline=False
        )
    else:
        min_, max_ = selected_weapon["cost"]
        overall_cost = round((max_ - cost) / (max_ - min_) * 100, 2)
        custom_embed.add_field(name="Cost Quality", value=f"{overall_cost}%", inline=False)
        base_stat += overall_cost

    if stat1 is None or stat1 < selected_weapon["stat1"][0] or stat1 > selected_weapon["stat1"][1]:
        custom_embed.add_field(
            name="Invalid stat 1", value="Please input correct weapon stat or use auto detect", inline=False
        )
    else:
        min_, max_ = selected_weapon["stat1"]
        overall_stat1 = round((stat1 - min_) / (max_ - min_) * 100, 2)
        custom_embed.add_field(name="Stat 1 Quality", value=f"{overall_stat1}%", inline=False)
        base_stat += overall_stat1

    if total_stat >= 2:
        if stat2 is None or stat2 < selected_weapon["stat2"][0] or stat2 > selected_weapon["stat2"][1]:
            custom_embed.add_field(
                name="Invalid stat 2", value="Please input correct weapon stat or use auto detect", inline=False
            )
        else:
            min_, max_ = selected_weapon["stat2"]
            overall_stat2 = round((stat2 - min_) / (max_ - min_) * 100, 2)
            custom_embed.add_field(name="Stat 2 Quality", value=f"{overall_stat2}%", inline=False)
            base_stat += overall_stat2

    if total_stat >= 3:
        if stat3 is None or stat3 < selected_weapon["stat3"][0] or stat3 > selected_weapon["stat3"][1]:
            custom_embed.add_field(
                name="Invalid stat 3", value="Please input correct weapon stat or use auto detect", inline=False
            )
        else:
            min_, max_ = selected_weapon["stat3"]
            overall_stat3 = round((stat3 - min_) / (max_ - min_) * 100, 2)
            custom_embed.add_field(name="Stat 3 Quality", value=f"{overall_stat3}%", inline=False)
            base_stat += overall_stat3

    if total_stat >= 4:
        if stat4 is None or stat4 < selected_weapon["stat4"][0] or stat4 > selected_weapon["stat4"][1]:
            custom_embed.add_field(
                name="Invalid stat 4", value="Please input correct weapon stat or use auto detect", inline=False
            )
        else:
            min_, max_ = selected_weapon["stat4"]
            overall_stat4 = round((stat4 - min_) / (max_ - min_) * 100, 2)
            custom_embed.add_field(name="Stat 4 Quality", value=f"{overall_stat4}%", inline=False)
            base_stat += overall_stat4

    max_stat = round((base_stat + 100) / (total_stat + 2), 2)
    min_stat = round(base_stat / (total_stat + 2), 2)
    max_ignore_passive = round(base_stat / (total_stat + 1), 2)
    max_with_2stat = round((base_stat + 200) / (total_stat + 3), 2)
    min_with_2stat = round(base_stat / (total_stat + 3), 2)

    for number, data in certified_detail:
        if max_stat >= number:
            (rarity, colour, emoji) = data
            break

    custom_embed.add_field(name="Max stat", value=f"**{max_stat}%**", inline=False)
    custom_embed.add_field(name="Rarity", value=f"**{rarity}** {emoji}", inline=False)
    custom_embed.add_field(
        name="Other info",
        value=f"Minimum stat: **{min_stat}%**\n"
        f"Maximum stat ignoring passive: **{max_ignore_passive}%**\n"
        f"Minimum stat with 2 stat passive: **{min_with_2stat}%**\n"
        f"Maximum stat with 2 stat passive: **{max_with_2stat}%**",
    )
    if colour is not None:
        custom_embed.colour = colour

    if image_url is not None:
        custom_embed.set_thumbnail(url=image_url)

    return custom_embed


async def visual_stat(ctx, level, hp, strength, pr, wp, mag, mr):
    blue = 0x00FFFF
    ehp, eatt, epr = '<:hp:759752326973227029>', '<:att:759752341678194708>', '<:pr:759752354467414056>'
    ewp, emag, emr = '<:wp:759752292713889833>', '<:mag:759752304080715786>', '<:mr:759752315904196618>'
    if hp == '.':
        hp_stat = 500 + level * 2
    elif hp.isdigit():
        hp = int(hp)
        hp_stat = 500 + hp * level * 2
    else:
        await ctx.send('Please input correct hp, use \'.\' as 1 stat ')
        return

    if strength == '.':
        str_stat = 100 + level
    elif strength.isdigit():
        strength = int(strength)
        str_stat = 100 + strength * level
    else:
        await ctx.send('Please input correct str, use \'.\' as 1 stat ')
        return

    if pr == '.':
        pr_stat = round((25 + (2 * level)) / (125 + (2 * level)) * 0.8 * 100)
    elif pr.isdigit():
        pr = int(pr)
        pr_stat = round((25 + (2 * pr * level)) / (125 + (2 * pr * level)) * 0.8 * 100)
    else:
        await ctx.send('Please input correct pr, use \'.\' as 1 stat ')
        return

    if wp == '.':
        wp_stat = 500 + level * 2
    elif wp.isdigit():
        wp = int(wp)
        wp_stat = 500 + wp * level * 2
    else:
        await ctx.send('Please input correct wp, use \'.\' as 1 stat ')
        return

    if mag == '.':
        mag_stat = 100 + level
    elif mag.isdigit():
        mag = int(mag)
        mag_stat = 100 + mag * level
    else:
        await ctx.send('Please input correct mag, use \'.\' as 1 stat ')
        return

    if mr == '.':
        mr_stat = round((25 + (2 * level)) / (125 + (2 * level)) * 0.8 * 100)
    elif mr.isdigit():
        mr = int(mr)
        mr_stat = round((25 + (2 * mr * level)) / (125 + (2 * mr * level)) * 0.8 * 100)
    else:
        await ctx.send('Please input correct mr, use \'.\' as 1 stat ')
        return

    if hp >= 8:
        category1 = 'Tank'
        if 3 <= wp <= 5:
            category = 'Energize'
        elif wp >= 6:
            category = 'Regen'
        else:
            category = 'Bad'
    elif strength >= 9:
        category = 'Str'
        if wp >= 3:
            category1 = 'Support'
        elif strength >= 11:
            category1 = 'Attacker'
        else:
            category1 = 'Bad'
    elif mag >= 7:
        category = 'Mag'
        if mag <= 10 and wp >= 3:
            category1 = 'Healer'
        elif mag >= 11:
            category1 = 'Attacker'
        else:
            category1 = 'Bad'
    else:
        category, category1 = '-', '-'
    custom_embed = discord.Embed(
        title=' Pet Stats',
        description=f'{ehp} `{hp_stat}`  {eatt} `{str_stat}`  {epr} `{pr_stat}%`\n'
        f'{ewp} `{wp_stat}`  {emag} `{mag_stat}`  {emr} `{mr_stat}%`',
        color=blue,
    )
    custom_embed.add_field(name='Category', value=f'{category} {category1}', inline=False)
    await ctx.send(embed=custom_embed)


class Anigame:
    def __init__(
        self,
        card_base_atk: int,
        card_def: int,
        enemy_base_atk: int,
        enemy_def: int,
        card_element: Optional[List[str]] = None,
        card_crit_multiplier: float = 1.75,
        enemy_element: Optional[List[str]] = None,
        enemy_crit_multiplier: float = 1.75,
    ):
        if card_element is None:
            card_element = ["neutral"]
        if enemy_element is None:
            enemy_element = ["neutral"]
        self.card = AnigameCard(card_base_atk, card_def, card_element, card_crit_multiplier)
        self.enemy_card = AnigameCard(enemy_base_atk, enemy_def, enemy_element, enemy_crit_multiplier)

    def damage(self, crit=False):
        return self.card.damage(self.enemy_card, crit)

    def enemy_damage(self, crit=False):
        return self.enemy_card.damage(self.card, crit)


class TalentButton(discord.ui.Button):
    def __init__(self, card: AnigameCard, **option):
        super().__init__(**option)
        self.card = card

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None and self.card.talent is not None
        view: AnigameView = self.view
        if interaction.user.id != self.view.user.id:
            return await interaction.response.send_message("You are not allowed to do this :c", ephemeral=True)
        self.card.talent.call_talent()
        await interaction.response.edit_message(content=f"Called {self.card.talent} talent", view=view, embed=view.display())


class AnigameDropdown(Dropdown):
    def __init__(
        self, text: str, select_list, original_view: AnigameView, card: AnigameCard, enemy: AnigameCard, change_type: str
    ):
        super().__init__(text, select_list)
        self.change_type = change_type
        self.original_view = original_view
        self.card = card
        self.enemy = enemy

    async def callback(self, interaction: discord.Interaction):
        assert self.original_view is not None
        view: AnigameView = self.original_view
        if self.change_type == "talent":
            self.card.talent = AnigameTalent(
                self.card, self.enemy, self.values[0].split(' ')[-1].lower(), self.values[0].split(' ')[0].lower()
            )
            if self.card == view.anigame.card and view.card_talent_button is None:
                button = TalentButton(self.card, label="Call card talent", style=discord.ButtonStyle.blurple)
                view.add_item(button)
                view.card_talent_button = button

            if self.card == view.anigame.enemy_card and view.enemy_talent_button is None:
                button = TalentButton(self.card, label="Call enemy talent", style=discord.ButtonStyle.blurple)
                view.add_item(button)
                view.enemy_talent_button = button

        if self.change_type == "rarity":
            self.card.rarity = STR_TO_RARITY[self.values[0].lower()]
        await view.message.delete()
        await interaction.response.edit_message(content="Done", view=None)
        message = await interaction.followup.send(view=view, embed=view.display())
        view.message = message  # type: ignore


class AnigameView(BaseView):
    card_talent_button: TalentButton
    enemy_talent_button: TalentButton
    message: discord.Message
    user: discord.User

    def __init__(self, anigame: Anigame):
        super().__init__()
        self.anigame: Anigame = anigame

    async def on_timeout(self) -> None:
        await super(AnigameView, self).on_timeout()
        await self.message.edit(content="Simulator timed out", view=None, embed=None)

    def display(self) -> discord.Embed:
        rarity_to_str = dict((v, k) for k, v in STR_TO_RARITY.items())
        custom_embed = discord.Embed(
            title="Anigame simulator",
            description=f"Damage: **{self.anigame.damage()}**\n"
            f"Crit damage: **{self.anigame.damage(True)}**\n"
            f"Enemy damage: **{self.anigame.enemy_damage()}**\n"
            f"Enemy crit damage **{self.anigame.enemy_damage(True)}**",
            color=discord.Colour.random(),
        )
        custom_embed.add_field(
            name=f"Self stat ({' '.join(RENDER_ELEMENT[em] for em in self.anigame.card.element)})",
            value=f"Base ATK: {self.anigame.card.base_atk}\n"
            f"ATK: "
            f"{self.anigame.card.atk * self.anigame.card.atk_percentage} "
            f"({self.anigame.card.atk} * {self.anigame.card.atk_percentage * 100}%)\n"
            f"DEF: "
            f"{self.anigame.card.defense * self.anigame.card.defense_percentage} "
            f"({self.anigame.card.atk} * {self.anigame.card.defense_percentage * 100}%)\n"
            f"Element multiplier: "
            f"{self.anigame.card.element_multiplier(self.anigame.enemy_card.element)}\n"
            f"Crit multiplier: {self.anigame.card.crit_multiplier}\n"
            f"Talent: **{self.anigame.card.talent or 'None :c'}**\n"
            f"**{rarity_to_str[self.anigame.card.rarity].capitalize()}**",
        )
        custom_embed.add_field(
            name=f"Enemy stat " f"({' '.join(RENDER_ELEMENT[em] for em in self.anigame.enemy_card.element)})",
            value=f"Base ATK: {self.anigame.enemy_card.base_atk}\n"
            f"ATK: "
            f"{self.anigame.enemy_card.atk * self.anigame.enemy_card.atk_percentage} "
            f"({self.anigame.enemy_card.atk} * "
            f"{self.anigame.enemy_card.atk_percentage * 100}%)\n"
            f"DEF: "
            f"{self.anigame.enemy_card.defense * self.anigame.enemy_card.defense_percentage} "
            f"({self.anigame.enemy_card.defense} * "
            f"{self.anigame.enemy_card.defense_percentage * 100}%)\n"
            f"Element multiplier: "
            f"{self.anigame.enemy_card.element_multiplier(self.anigame.card.element)}\n"
            f"Crit multiplier: {self.anigame.enemy_card.crit_multiplier}\n"
            f"Talent: **{self.anigame.enemy_card.talent or 'None :c'}**\n"
            f"**{rarity_to_str[self.anigame.enemy_card.rarity].capitalize()}**",
        )
        return custom_embed

    @discord.ui.button(label="Change card talent")  # type: ignore
    async def change_card_talent(self, interaction: discord.Interaction, _: discord.Button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(content="You are not allowed to use this >:(", ephemeral=True)
        another_view = BaseView()
        another_view.add_item(
            AnigameDropdown(
                text="Select talent",
                select_list=[
                    discord.SelectOption(label=s, value=s)
                    for s in [
                        "Defense Berserker",
                        "Atk Berserker",
                        "Defense Overload",
                        "Atk Overload",
                        "Defense Breaker",
                        "Atk Breaker",
                        "Defense Trick",
                        "Atk Trick",
                        "Atk Precision",
                    ]
                ],
                original_view=self,
                card=self.anigame.card,
                enemy=self.anigame.enemy_card,
                change_type="talent",
            )
        )
        await interaction.response.send_message(view=another_view, ephemeral=True)

    @discord.ui.button(label="Change enemy talent")  # type: ignore
    async def change_enemy_talent(self, interaction: discord.Interaction, _: discord.Button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(content="You are not allowed to use this >:(", ephemeral=True)
        another_view = BaseView()
        another_view.add_item(
            AnigameDropdown(
                text="Select talent",
                select_list=[
                    discord.SelectOption(label=s, value=s)
                    for s in [
                        "Defense Berserker",
                        "Atk Berserker",
                        "Defense Overload",
                        "Atk Overload",
                        "Defense Breaker",
                        "Atk Breaker",
                        "Atk Precision",
                    ]
                ],
                original_view=self,
                card=self.anigame.enemy_card,
                enemy=self.anigame.card,
                change_type="talent",
            )
        )
        await interaction.response.send_message(view=another_view, ephemeral=True)

    @discord.ui.button(label="Change card rarity")  # type: ignore
    async def change_card_rarity(self, interaction: discord.Interaction, _: discord.Button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(content="You are not allowed to use this >:(", ephemeral=True)
        another_view = BaseView()
        another_view.add_item(
            AnigameDropdown(
                text="Select rarity",
                select_list=[
                    discord.SelectOption(label=s, value=s)
                    for s in ["Common", "Uncommon", "Rare", "Super Rare", "Ultra Rare", "Legendary"]
                ],
                original_view=self,
                card=self.anigame.card,
                enemy=self.anigame.enemy_card,
                change_type="rarity",
            )
        )
        await interaction.response.send_message(view=another_view, ephemeral=True)

    @discord.ui.button(label="Change enemy rarity")  # type: ignore
    async def change_enemy_rarity(self, interaction: discord.Interaction, _: discord.Button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(content="You are not allowed to use this >:(", ephemeral=True)
        another_view = BaseView()
        another_view.add_item(
            AnigameDropdown(
                text="Select rarity",
                select_list=[
                    discord.SelectOption(label=s, value=s)
                    for s in ["Common", "Uncommon", "Rare", "Super Rare", "Ultra Rare", "Legendary"]
                ],
                original_view=self,
                card=self.anigame.enemy_card,
                enemy=self.anigame.card,
                change_type="rarity",
            )
        )
        await interaction.response.send_message(view=another_view, ephemeral=True)

    @discord.ui.button(label="Reset all")  # type: ignore
    async def reset_card(self, interaction: discord.Interaction, _: discord.Button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(content="You are not allowed to use this >:(", ephemeral=True)
        self.anigame.card.reset()
        self.anigame.enemy_card.reset()
        for child in self.children:
            if isinstance(child, TalentButton):
                self.remove_item(child)
        await interaction.response.edit_message(embed=self.display(), view=self)


# noinspection SpellCheckingInspection
class HelperCommand(commands.Cog):
    def __init__(self, bot: SewentyBot):
        self.bot: SewentyBot = bot

    @commands.command(aliases=["wstat", "statw", "wcheck"])
    async def maxwstat(
        self,
        ctx: commands.Context,
        weapon_type: Optional[str] = None,
        cost: Optional[int] = None,
        stat1: Optional[float] = None,
        stat2: Optional[float] = None,
        stat3: Optional[float] = None,
        stat4: Optional[float] = None,
    ):
        if weapon_type is not None:
            return await ctx.send(embed=max_weapon_stat(weapon_type, cost, stat1, stat2, stat3, stat4))  # type: ignore

        ref = ctx.message.reference
        msg = None
        if (
            ref is not None
            and isinstance(ref.resolved, discord.Message)
            and ref.resolved.author.id == 408785106942164992
            and ref.resolved.embeds
        ):
            msg = ref.resolved

        if msg is None:
            async for message in ctx.message.channel.history(limit=5):
                if message.author.id == 408785106942164992 and message.embeds:
                    msg = message
                    break
        embeds = msg.embeds if msg is not None else []
        if len(embeds) < 1:
            return await ctx.reply(
                "Please input weapon type. You can either reply to embed " "or check for 5 messages before you",
                mention_author=False,
            )
        last: discord.Embed = embeds[-1]
        if last.description is None:
            return
        new = last.description.split('\n')
        weapon_type = new[0].split("**")[2].lower()
        cost = int(new[5].split("**")[2].split(' ')[1])
        if not ("banner" in weapon_type or "aegis" in weapon_type or "celebration" in weapon_type):
            stat1 = float(new[6].split("**")[3].replace('%', ''))
        if "great" in weapon_type.lower():
            weapon_type = "sword"
        elif "healing" in weapon_type:
            weapon_type = "hstaff"
        elif "defender" in weapon_type:
            weapon_type = "aegis"
            stat1 = float(new[8].split("**")[-2])
        elif "vampiric" in weapon_type:
            weapon_type = "vstaff"
        elif "energy" in weapon_type:
            weapon_type = "estaff"
        elif "poison" in weapon_type:
            weapon_type = "dagger"
            stat2 = float(new[8].split("**")[3].replace('%', ''))
        elif "wand" in weapon_type:
            weapon_type = "wand"
            stat2 = float(new[6].split("**")[-2].replace('%', ''))
        elif "flame" in weapon_type:
            weapon_type = "fstaff"
            stat2 = float(new[8].split("**")[3].replace('%', ''))
            stat3 = float(new[8].split("**")[-2].replace('%', ''))
        elif "spirit" in weapon_type:
            weapon_type = "sstaff"
            stat2 = float(new[8].split("**")[-2].replace('%', ''))
        elif "scepter" in weapon_type:
            weapon_type = "scepter"
        elif "resurrection" in weapon_type:
            weapon_type = "rstaff"
        elif "glacial" in weapon_type:
            weapon_type = 'axe'
        elif "banner" in weapon_type:
            weapon_type = "banner"
            stat1 = float(new[8].split("**")[-2].replace('%', ''))
            stat2 = float(new[9].split("**")[-2].replace('%', ''))
            stat3 = float(new[10].split("**")[-2].replace('%', ''))
        elif "culling" in weapon_type:
            weapon_type = "scythe"
            stat2 = float(new[8].split("**")[-2].replace('%', ''))
        elif "bow" in weapon_type:
            weapon_type = "bow"
        elif "purity" in weapon_type:
            weapon_type = "pstaff"
            stat2 = float(new[6].split("**")[-2].replace('%', ''))
        elif "celebration" in weapon_type:
            weapon_type = "crune"
            stat1 = float(new[8].split("**")[3].replace('%', ''))
            stat2 = float(new[8].split("**")[-2].replace('%', ''))
        elif "leeching" in weapon_type:
            weapon_type = "lscythe"
            stat2 = float(new[6].split("**")[-2].replace('%', ''))
            stat3 = float(new[8].split("**")[3].replace('%', ''))
            stat4 = float(new[8].split("**")[-2].replace('%', ''))

        return await ctx.send(embed=max_weapon_stat(weapon_type, cost, stat1, stat2, stat3, stat4))  # type: ignore

    @maxwstat.error
    async def maxwstat_on_error(self, ctx, error):
        if isinstance(error, commands.errors.CommandInvokeError):
            if isinstance(error.original, IndexError):
                return await ctx.send(
                    "Failed to parse stat. " "Perhaps you replied wrong embed or detected wrong last embed"
                )
            return await ctx.send(f"Failed to parse stat: `{error.original}`")
        if isinstance(error, commands.errors.DisabledCommand):
            return
        return await ctx.send(f"Failed to parse stat: `{error}`")

    @commands.command(aliases=["statpet", "petlevel", "levelpet"])
    async def petstat(self, ctx, level=None, hp=None, strength=None, pr=None, wp=None, mag=None, mr=None):
        """
        Visualize pet stat in cettin level
        """
        if level is not None and level.isdigit():
            level = int(level)
            if hp and strength and pr and wp and mag and mr:
                await visual_stat(ctx, level, hp, strength, pr, wp, mag, mr)
            elif not (hp or strength or pr or wp or mag or mr):
                async for x in ctx.message.channel.history(limit=3):
                    if x.author.id == 408785106942164992:
                        embeded = x.embeds
                        y = {}
                        for y in embeded:
                            y = y.to_dict()
                        new = y['description'].split('`')
                        if len(new) != 13:
                            return
                        hp, strength, pr, wp, mag, mr = [new[z] for z in range(1, 12, 2)]
                        await visual_stat(ctx, level, hp, strength, pr, wp, mag, mr)
                        return
                    elif x.author.id == 750534176666550384:
                        embeded = x.embeds
                        y = {}
                        for y in embeded:
                            y = y.to_dict()
                        new = y['fields'][1]['value'].split('`')
                        hp, strength, pr, wp, mag, mr = [new[z] for z in range(1, 12, 2)]
                        await visual_stat(ctx, level, hp, strength, pr, wp, mag, mr)
                        return
                await ctx.reply('Please input complete stat', mention_author=False)

            else:
                await ctx.reply(
                    'Please input complete stat `<level> <hp> <str> <pr> <wp> <mag> <mr>` , use \'.\' as 1 stat',
                    mention_author=False,
                )
        else:
            await ctx.reply('Invalid argument :c', mention_author=False)

    @commands.command(aliases=["ulog"])
    async def ultralog(self, ctx):
        # if ctx.author.id in restricted:
        #     return
        async for x in ctx.message.channel.history(limit=3):
            if x.author.id != 555955826880413696:
                continue
            embedded = x.embeds
            if embedded is None or len(embedded) < 1:
                continue
            y = embedded[-1].to_dict()
            if 'inventory' in y['author']['name']:
                inventory_dict = y['fields'][0]['value'].split("**")
                log_data = {}
                for z in range(len(inventory_dict)):
                    if ' log' in inventory_dict[z]:
                        log_data.update(
                            {
                                inventory_dict[z].lower(): int(
                                    inventory_dict[z + 1].replace(': ', '').split('\n')[0].replace(',', '')
                                )
                            }
                        )
                # calcuating
                solution = ''
                solution_crafter = ''
                hyper_log, mega_log, super_log, epic_log, wooden_log = [0 for _ in range(5)]

                if 'hyper log' in log_data:
                    if log_data['hyper log'] >= 10:
                        solution = 'rpg craft ultra log'
                        solution_crafter = solution
                    else:
                        hyper_log = log_data['hyper log']
                if 'mega log' in log_data:
                    mega_log = log_data['mega log']
                    if not solution:
                        required_log = 10 - hyper_log
                        if mega_log >= required_log * 10:
                            solution = f'rpg craft hyper log {required_log}\n' f'rpg craft ultra log'
                            solution_crafter = solution
                if 'super log' in log_data:
                    super_log = log_data['super log']
                    if not solution:
                        required_log = (10 - hyper_log) * 10 - mega_log
                        if super_log >= required_log * 10:
                            solution = (
                                f'rpg craft mega log {required_log}\n' f'rpg craft hyper log all\n' f'rpg craft ultra log'
                            )
                if 'epic log' in log_data:
                    epic_log = log_data['epic log']
                    if not solution:
                        required_log = (10 - hyper_log) * 100 - mega_log * 10 - super_log
                        if epic_log >= required_log * 10:
                            solution = (
                                f'rpg craft super log {required_log}\n'
                                f'rpg craft mega log all\n'
                                f'rpg craft hyper log all\n'
                                f'rpg craft ultra log'
                            )
                if 'wooden log' in log_data:
                    wooden_log = log_data['wooden log']
                    if not solution:
                        required_log = (10 - hyper_log) * 1000 - mega_log * 100 - super_log * 10 - epic_log
                        if wooden_log >= required_log * 25:
                            solution = (
                                f'rpg craft epic log {required_log}\n'
                                f'rpg craft super log all\n'
                                f'rpg craft mega log all\n'
                                f'rpg craft hyper log all\n'
                                f'rpg craft ultra log'
                            )
                        else:
                            await ctx.send(f'You need at least {required_log * 25 - wooden_log} wooden log to do this')
                            break
                elif not solution:
                    await ctx.send("No solution found")
                    break
                calculator = discord.Embed(
                    title='Efficiency Calculation',
                    description='**Crafter Solution still on test so it maybe wrong** '
                    'Feel free to suggest efficient way for crafter',
                    color=7864132,
                )
                calculator.add_field(name='Non crafter', value=solution)
                await ctx.send(embed=calculator)

                if not solution_crafter:

                    def verify(m):
                        if (
                            m.author == ctx.author
                            and m.content.lower() in ["y", "n", "yes", "no"]
                            and m.channel.id == ctx.channel.id
                        ):
                            if m.content.lower() in ["no", "n"]:
                                raise asyncio.TimeoutError
                            return True
                        return False

                    await ctx.send("Would you like to calculate for crafter solution? (y/n)\n" "Aborting in 10 seconds")
                    try:
                        await self.bot.wait_for("message", check=verify, timeout=10)
                    except asyncio.TimeoutError:
                        await ctx.send("Aborting")
                        break

                    def verify2(m):
                        if m.author == ctx.author and m.channel.id == ctx.channel.id:
                            try:
                                float(m.content)
                                return True
                            except OverflowError:
                                pass
                            except ValueError:
                                pass
                        return False

                    await ctx.send("Gib your current percentage of returned item. Aborting in 15 seconds")
                    try:
                        returned_item = await self.bot.wait_for("message", check=verify2, timeout=15)
                    except asyncio.TimeoutError:
                        await ctx.send("Aborting")
                        break
                    returned_item = float(returned_item.content) / 100
                    original = await ctx.send("Calculating <a:discordloading:792012369168957450>")
                    async with ctx.typing():
                        pass
                    solved = False
                    tier = ["hyper log", "mega log", "super log", "epic log"]
                    dump = 0
                    amount = 0
                    t1 = time.time()
                    while not solved:
                        if hyper_log >= 10:
                            if dump != 0 and amount != 0:
                                solution_crafter += f"\n{tier[dump - 1]} {amount}"
                                dump, amount = 0, 0
                            solution_crafter += "\nultra log"
                            solved = True

                        elif mega_log >= 10:
                            if dump != 1 and amount != 0:
                                solution_crafter += f"\n{tier[dump - 1]} {amount}"
                                dump, amount = 0, 0
                            if mega_log >= (10 - hyper_log) * 10:
                                dump = 1
                                amount += 10 - hyper_log
                                # actually useless but whatever
                                mega_log -= (10 - hyper_log) * 10 - floor((100 - 10 * hyper_log) * returned_item)
                                hyper_log = 10
                            else:
                                solution_crafter += f"\nhyper log all"
                                hyper_log += floor(mega_log / 10)
                                mega_log = (mega_log % 10) + floor(floor(mega_log / 10) * 10 * returned_item)

                        elif super_log >= 10:
                            if dump != 2 and amount != 0:
                                solution_crafter += f"\n{tier[dump - 1]} {amount}"
                                dump, amount = 0, 0
                            if super_log >= (100 - 10 * hyper_log - mega_log) * 10:
                                dump = 2
                                amount += 100 - 10 * hyper_log - mega_log
                                super_log -= (100 - 10 * hyper_log - mega_log) * 10 - floor(
                                    (100 - 10 * hyper_log - mega_log) * 10 * returned_item
                                )
                                mega_log = 100 - 10 * hyper_log

                            else:
                                solution_crafter += f"\nmega log all"
                                mega_log += floor(super_log / 10)
                                super_log = (super_log % 10) + floor(floor(super_log / 10) * 10 * returned_item)
                        elif epic_log >= 10:
                            if dump != 3 and amount != 0:
                                solution_crafter += f"\n{tier[dump - 1]} {amount}"
                                dump, amount = 0, 0
                            if epic_log >= (100 - 10 * mega_log - super_log) * 10:
                                dump = 3
                                amount += 100 - 10 * mega_log - super_log
                                epic_log -= (100 - 10 * mega_log - super_log) * 10 - floor(
                                    (100 - 10 * mega_log - super_log) * 10 * returned_item
                                )
                                super_log = 100 - 10 * mega_log
                            else:
                                solution_crafter += f"\nsuper log all"
                                super_log += floor(epic_log / 10)
                                epic_log = (epic_log % 10) + floor(floor(epic_log / 10) * 10 * returned_item)
                        else:
                            if dump != 4 and amount != 0:
                                solution_crafter += f"\n{tier[dump - 1]} {amount}"
                                dump, amount = 0, 0
                            dump = 4
                            if wooden_log >= (100 - 10 * super_log - epic_log) * 25:
                                wooden_log -= (100 - 10 * super_log - epic_log) * 25 - floor(
                                    (100 - 10 * super_log - epic_log) * 25 * returned_item
                                )
                                amount += 100 - 10 * super_log - epic_log
                                epic_log = 100 - 10 * super_log
                            elif wooden_log >= 25:
                                solution_crafter += f"\nepic log all"
                                epic_log += floor(wooden_log / 25)
                                wooden_log = (wooden_log % 25) + floor(floor(wooden_log / 25) * 25 * returned_item)
                            else:
                                await ctx.send("OwO what is this? solution not found. Aborting..")
                                break

                    # O(N^2) !!
                    async def reduce(arr):
                        i = 0
                        while i < len(arr):
                            start = arr[i]
                            length = 0
                            count = 1
                            sub_string = None

                            for j in range(i + 1, len(arr)):
                                end = arr[j]
                                if start == end:
                                    length = j - i
                                    sub_string = arr[i:j]
                                    break
                            # skip if not found
                            if length == 0 and sub_string is None:
                                i += 1
                                continue

                            # continue capture substring
                            check = i + length
                            while len(arr) >= check + length and arr[check : check + length] == sub_string:
                                count += 1
                                check += length
                            if count == 1:
                                i += 1
                                continue
                            if length > 5:
                                sub_string = await reduce(sub_string)  # type: ignore
                            if length > 5:
                                sub_string = (
                                    f"----- S T A R T ----- \n"
                                    f"{sub_string}\n"
                                    f"----- E N D ----- **(Repeat {count} times)**"
                                )
                            else:
                                sub_string = f"({' >> '.join(sub_string)})-> **{count} times**"
                            arr = arr[0:i] + [sub_string] + arr[check : len(arr)]
                            i += 1

                        reduced = '\n'.join(arr)
                        return reduced

                    # try to reduce the repeated string
                    raw = solution_crafter.strip().split('\n')
                    solution_crafter = await reduce(raw)

                    try:
                        if len(solution_crafter) > 2000:

                            async def divide_string(string):
                                if len(string) > 2000:
                                    s1 = len(string) // 2
                                    s2 = s1
                                    while string[s1] != '\n':
                                        s1 += 1
                                        s2 += 1
                                    await divide_string(string[:s1])  # type: ignore
                                    await divide_string(string[s2:])  # type: ignore
                                else:
                                    await ctx.send(string)

                            await divide_string(solution_crafter)
                            await ctx.send(f"Elapsed time: {time.time() - t1}s")
                        else:
                            await original.edit(content=solution_crafter)
                            await ctx.send(f"Elapsed time: {time.time() - t1}s")
                    except discord.HTTPException:
                        await original.edit(content="Character limit reached")

    @commands.command(aliases=["streakcount", "bonusxp", "countxp"])
    async def countstreak(self, ctx, streak: Optional[int] = None):
        """
        Count xp bonus based on streaks
        """
        yellow = 0xFFF00
        if streak is None:
            streak = random.randint(1, 100000)
        if streak % 1000 == 0:
            bonus = 25 * (pow(streak / 100, 1 / 2) * 100 + 500)
        elif streak % 500 == 0:
            bonus = 10 * (pow(streak / 100, 1 / 2) * 100 + 500)
        elif streak % 100 == 0:
            bonus = 5 * (pow(streak / 100, 1 / 2) * 100 + 500)
        elif streak % 50 == 0:
            bonus = 3 * (pow(streak / 100, 1 / 2) * 100 + 500)
        elif streak % 10 == 0:
            bonus = pow(streak / 100, 1 / 2) * 100 + 500
        else:
            bonus = 0
        bonus = round(bonus)
        if bonus > 100000:
            bonus = 100000
        decoration = random.randint(1, 20)
        name = ctx.author.name
        custom_embed = discord.Embed(
            title=f'{name} goes into battle!',
            description=f'You won in {decoration} '
            f'turns! your team gained '
            f'**200 + {bonus}** xp! '
            f'streak: {streak}',
            color=yellow,
        )
        await ctx.send(embed=custom_embed)

    @commands.command(aliases=["astat"])
    async def anigamestat(
        self,
        ctx,
        card_base_atk: int,
        card_def: int,
        enemy_base_atk: int,
        enemy_def: int,
        card_crit_multiplier: Optional[float] = 1.75,
        enemy_crit_multiplier: Optional[float] = 1.75,
        *,
        elements: str = "neutral neutral",  # type: ignore
    ):
        card_base_atk *= 10
        card_def *= 10
        enemy_base_atk *= 10
        enemy_def *= 10
        if '|' in elements:
            elements = elements.split('|')
        elif ',' in elements:
            elements = elements.split(',')
        else:
            elements = elements.split(' ')

        elements: List
        card_element: List
        enemy_element: List

        if len(elements) > 3:
            card_element = elements[0:3]
            enemy_element = elements[3:6]
        else:
            card_element = elements[0:-1]
            enemy_element = elements[-1:0:-1]

        anigame = Anigame(
            card_base_atk,
            card_def,
            enemy_base_atk,
            enemy_def,
            card_element,
            card_crit_multiplier,  # type: ignore
            enemy_element,
            enemy_crit_multiplier,  # type: ignore
        )  

        view = AnigameView(anigame)
        view.user = ctx.author
        msg = await ctx.send(embed=view.display(), view=view)
        view.message = msg


async def setup(bot: SewentyBot):
    await bot.add_cog(HelperCommand(bot))
