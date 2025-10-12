import discord
from embeds.dnd.abstract import HORIZONTAL_LINE, DNDObjectEmbed
from logic.config import is_source_phb2014
from logic.dnd.class_ import Class


class MultiClassSubclassSelect(discord.ui.Select):
    """Select component to provide a Subclass-dropdown under a ClassEmbed"""

    def __init__(
        self,
        character_class: Class,
        get_level: callable,
        subclass: str,
        parent_view: "ClassNavigationView",
    ):
        options = []
        for subclass_name in character_class.subclass_level_features.keys():
            if is_source_phb2014(character_class.source) and subclass_name.endswith("(PHB)"):
                continue  # Only show PHB subclasses for PHB classes

            label = subclass_name if subclass != subclass_name else f"{subclass_name} [Current]"
            options.append(discord.SelectOption(label=label, value=subclass_name))

        super().__init__(placeholder="Select Subclass", min_values=1, max_values=1, options=options)

        self.character_class = character_class
        self.get_level = get_level
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        subclass = self.values[0]
        self.parent_view.subclass = subclass
        level = self.get_level()
        embed = ClassEmbed(self.character_class, level, subclass)
        await interaction.response.edit_message(embed=embed, view=embed.view)


class MultiClassPageSelect(discord.ui.Select):
    """Select component to quickly navigate between class-pages (base info or level info)"""

    def __init__(
        self,
        character_class: Class,
        get_subclass: callable,
        page: int,
        parent_view: "ClassNavigationView",
    ):
        options = []
        core_label = "Core Info" if page != 0 else "Core Info [Current]"
        options.append(discord.SelectOption(label=core_label, value="0"))
        for level in character_class.level_resources.keys():
            label = f"Level {level}" if int(level) != page else f"Level {level} [Current]"
            options.append(discord.SelectOption(label=label, value=level))

        super().__init__(placeholder="Select Level", min_values=1, max_values=1, options=options)

        self.character_class = character_class
        self.get_subclass = get_subclass
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        level = int(self.values[0])
        self.parent_view.level = level
        subclass = self.get_subclass()
        embed = ClassEmbed(self.character_class, level, subclass)
        await interaction.response.edit_message(embed=embed, view=embed.view)


class ClassNavigationView(discord.ui.View):
    level: int
    subclass: str | None

    def __init__(self, character_class: Class, level: int, subclass: str | None):
        super().__init__()

        self.character_class = character_class
        self.level = level
        self.subclass = subclass

        if character_class.level_resources:
            self.add_item(MultiClassPageSelect(self.character_class, lambda: self.subclass, self.level, self))
        if character_class.subclass_level_features:
            self.add_item(MultiClassSubclassSelect(self.character_class, lambda: self.level, self.subclass, self))


class ClassEmbed(DNDObjectEmbed):
    def __init__(self, character_class: Class, level: int = 0, subclass: str | None = None):
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
        self.view = ClassNavigationView(character_class, level, subclass)
