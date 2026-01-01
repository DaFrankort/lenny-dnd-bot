import discord

from embeds.dnd.abstract import HORIZONTAL_LINE, DNDEntryEmbed
from logic.dnd.class_ import Class


class MultiClassSubclassSelect(discord.ui.Select["ClassNavigationView"]):
    """Select component to provide a Subclass-dropdown under a ClassEmbed"""

    def __init__(
        self,
        character_class: Class,
        level: int,
        subclass: str | None,
        parent_view: "ClassNavigationView",
    ):
        sources = [f"({src})" for src in parent_view.allowed_sources]
        options: list[discord.SelectOption] = []
        for subclass_name in character_class.subclasses:
            if not any(src in subclass_name for src in sources):
                continue  # Skip disallowed source-content.
            if character_class.source == "XPHB" and "(PHB)" in subclass_name:
                continue  # Do not show PHB subclasses for XPHB classes, unreliable data.

            label = subclass_name if subclass != subclass_name else f"{subclass_name} [Current]"
            options.append(discord.SelectOption(label=label, value=subclass_name))

        super().__init__(placeholder="Select Subclass", min_values=1, max_values=1, options=options)

        self.character_class = character_class
        self.level = level
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        subclass = self.values[0]
        self.parent_view.subclass = subclass
        embed = ClassEmbed(self.character_class, self.parent_view.allowed_sources, self.level, subclass)
        await interaction.response.edit_message(embed=embed, view=embed.view)


class MultiClassPageSelect(discord.ui.Select["ClassNavigationView"]):
    """Select component to quickly navigate between class-pages (base info or level info)"""

    def __init__(
        self,
        character_class: Class,
        subclass: str | None,
        page: int,
        parent_view: "ClassNavigationView",
    ):
        options: list[discord.SelectOption] = []
        core_label = "Core Info" if page != 0 else "Core Info [Current]"
        options.append(discord.SelectOption(label=core_label, value="0"))
        for level in character_class.level_resources.keys():
            label = f"Level {level}" if int(level) != page else f"Level {level} [Current]"
            options.append(discord.SelectOption(label=label, value=level))

        super().__init__(placeholder="Select Level", min_values=1, max_values=1, options=options)

        self.character_class = character_class
        self.subclass = subclass
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        level = int(self.values[0])
        self.parent_view.level = level
        embed = ClassEmbed(self.character_class, self.parent_view.allowed_sources, level, self.subclass)
        await interaction.response.edit_message(embed=embed, view=embed.view)


class ClassNavigationView(discord.ui.View):
    character_class: Class
    allowed_sources: set[str]
    level: int
    subclass: str | None

    def __init__(self, character_class: Class, allowed_sources: set[str], level: int, subclass: str | None):
        super().__init__()

        self.character_class = character_class
        self.allowed_sources = allowed_sources
        self.level = level
        self.subclass = subclass

        if character_class.level_resources:
            self.add_item(MultiClassPageSelect(self.character_class, self.subclass, self.level, self))
        if character_class.subclass_level_features:
            self.add_item(MultiClassSubclassSelect(self.character_class, self.level, self.subclass, self))


class ClassEmbed(DNDEntryEmbed):
    def __init__(self, character_class: Class, allowed_sources: set[str], level: int = 0, subclass: str | None = None):
        # Check if given subclass is valid
        if subclass and not character_class.has_subclass(subclass):
            raise ValueError(
                f"Class {character_class.name} ({character_class.source}) does not have '{subclass}' as a subclass!"
            )

        level = max(0, min(20, level))

        super().__init__(character_class)

        if level == 0:  # Core Info (page 0)
            self.description = "*Core Info*"

            if character_class.primary_ability:
                self.add_field(
                    name="Primary Ability",
                    value=character_class.primary_ability,
                    inline=True,
                )
            if character_class.spellcast_ability:
                self.add_field(
                    name="Spellcast Ability",
                    value=character_class.spellcast_ability,
                    inline=True,
                )

            self.add_description_fields(character_class.base_info)

        else:
            subtitle = f"Level {level}"
            if subclass and level >= (character_class.subclass_unlock_level or 0):
                subtitle += f" {subclass}"
            self.description = f"*{subtitle}*"

            # Level Resources are handled differently, since we want inline fields here.
            level_resources = character_class.level_resources.get(str(level), [])
            for resource in level_resources:
                name = resource["name"]
                if resource["type"] == "table":
                    value = self.build_table(resource["value"])
                    inline = False
                else:
                    value = resource["value"]
                    inline = True

                self.add_field(name=name, value=value, inline=inline)

            # Rest of the descriptions
            descriptions = character_class.level_features.get(str(level), []).copy()
            if subclass:
                subclass_level_descriptions = character_class.subclass_level_features.get(subclass, {})
                subclass_description = subclass_level_descriptions.get(str(level), []).copy()
                descriptions.extend(subclass_description)

            if descriptions:
                self.add_field(name="", value=HORIZONTAL_LINE, inline=False)
                self.add_description_fields(descriptions=descriptions)

        self.set_footer(text=f"Page {level + 1} / 21", icon_url="")
        self.view = ClassNavigationView(character_class, allowed_sources, level, subclass)
