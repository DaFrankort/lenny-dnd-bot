from collections.abc import Sequence

import discord
from discord import ui

from embeds.components import BaseSeparator, TitleTextDisplay
from logic.charactergen import (
    CharacterGenResult,
    format_modifier_str,
    get_mod_from_score,
)
from logic.charts import get_radar_chart
from logic.color import UserColor
from logic.dnd.abstract import DNDEntry, build_table_from_rows
from logic.dnd.background import Background
from logic.dnd.name import Gender


class _CharacterGenInfoButton(ui.Button["CharacterGenContainerView"]):
    def __init__(self, entry: DNDEntry, emoji: str):
        style = discord.ButtonStyle.url
        super().__init__(style=style, label=entry.name, emoji=emoji, url=entry.url)


class CharacterGenContainerView(ui.LayoutView):
    chart: discord.File

    def _build_ability_table(
        self,
        background: Background,
        stats: list[tuple[int, str]],
        boosted_stats: list[tuple[int, str]],
    ):
        headers = ["Ability", "Score", "Mod"]
        rows: list[Sequence[str]] = []
        for stat, boosted in zip(stats, boosted_stats):
            base_value, name = stat
            boosted_value, _ = boosted

            bg_abilities = [f"{a[:3].lower()}." for a in background.abilities]
            if name.lower() in bg_abilities:
                name += "*"  # mark bg abilities

            ability_value = str(base_value)
            if boosted_value != base_value:
                diff = boosted_value - base_value
                ability_value = f"{base_value} + {diff}"

            mod = get_mod_from_score(boosted_value)
            mod = format_modifier_str(mod, True)

            rows.append([name, ability_value, mod])

        return build_table_from_rows(headers=headers, rows=rows)

    def __init__(self, result: CharacterGenResult):
        super().__init__(timeout=None)
        color = discord.Color(UserColor.generate(result.name))
        container = ui.Container[CharacterGenContainerView](accent_color=color)
        container.add_item(TitleTextDisplay(result.name))

        btn_row = ui.ActionRow[CharacterGenContainerView]()
        species_emoji = "🧝‍♀️" if result.gender is Gender.FEMALE else "🧝‍♂️"
        btn_row.add_item(_CharacterGenInfoButton(result.species, species_emoji))
        class_emoji = "🧙‍♀️" if result.gender is Gender.FEMALE else "🧙‍♂️"
        btn_row.add_item(_CharacterGenInfoButton(result.char_class, class_emoji))
        bg_emoji = "📕" if result.gender is Gender.FEMALE else "📘"
        btn_row.add_item(_CharacterGenInfoButton(result.background, bg_emoji))
        container.add_item(btn_row)

        container.add_item(BaseSeparator())
        container.add_item(ui.TextDisplay(result.backstory))
        container.add_item(BaseSeparator())

        ability_table = self._build_ability_table(result.background, result.stats, result.boosted_stats)
        total = sum(val for val, _ in result.stats)
        ability_desc = ability_table + f"\n**Total**: {total} + 3"

        values = [stat[0] for stat in result.stats]
        labels = [stat[1] for stat in result.stats]
        boosts = [stat[0] for stat in result.boosted_stats]
        self.chart = get_radar_chart(values=values, labels=labels, boosts=boosts, color=color.value)
        ability_image = ui.Thumbnail[CharacterGenContainerView](media=self.chart)
        ability_section = ui.Section[CharacterGenContainerView](ability_desc, accessory=ability_image)
        container.add_item(ability_section)

        container.add_item(BaseSeparator())
        for info in self._get_additional_info(result):
            container.add_item(ui.TextDisplay(info))

        self.add_item(container)

    def _get_additional_info(self, result: CharacterGenResult) -> list[str]:
        info: list[str] = []
        derived = "### Derived Stats"
        derived += f"\n- ``{result.derived_stats.hp}`` Starting HP"
        derived += f"\n- ``+{result.derived_stats.proficiency}`` Proficiency Bonus"
        derived += f"\n- ``{format_modifier_str(result.derived_stats.initiative)}`` Initiative"

        if result.background.feat and "Alert" in result.background.feat:
            derived += " (Alert)"  # TODO handle this better.
            derived += f"\n- ``{result.derived_stats.speed}`` Movement Speed"
            derived += f"\n- ``{result.derived_stats.passive_perception}`` Passive Perception"
        info.append(derived)

        if result.spellcasting:
            spellcasting = f"### Spellcasting ({result.spellcasting.ability})"
            spellcasting += f"\n- ``{format_modifier_str(result.spellcasting.spell_mod)}`` Spellcasting Mod."
            spellcasting += f"\n- ``{result.spellcasting.spellsave_dc}`` Spellsave DC"
            spellcasting += f"\n- ``{format_modifier_str(result.spellcasting.spell_atk)}`` Spell Attack Mod."
            info.append(spellcasting)

        if result.proficiencies:
            prof = "### Skill Proficiencies\n"
            prof += ", ".join([p.title() for p in result.proficiencies])
            info.append(prof)

        if result.languages:
            languages = f"### Languages ({len(result.languages)})\n"
            languages += ", ".join(result.languages)
            info.append(languages)

        if result.starting_equipment:
            equipment = "### Starting Equipment"
            equipment += "\n- " + "\n- ".join(result.starting_equipment)
            info.append(equipment)

        return info
