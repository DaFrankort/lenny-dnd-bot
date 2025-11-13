import discord

from embeds.dnd.abstract import HORIZONTAL_LINE, DNDEntryEmbed
from logic.dnd.item import Item


class ItemEmbed(DNDEntryEmbed):
    def __init__(self, item: Item) -> None:
        super().__init__(item)

        value_weight = item.formatted_value_weight
        properties = item.formatted_properties
        type = item.formatted_type
        descriptions = item.description

        if type is not None:
            self._set_embed_color(item)
            self.add_field(name="", value=f"*{type}*", inline=False)

        if properties is not None:
            self.add_field(name="", value=properties, inline=False)

        if value_weight is not None:
            self.add_field(name="", value=value_weight, inline=False)

        if len(descriptions) > 0:
            # Add horizontal line
            self.add_field(
                name="",
                value=HORIZONTAL_LINE,
                inline=False,
            )

            self.add_description_fields(item.description)

    def _set_embed_color(self, item: Item):
        type_colors = {
            "common": discord.Colour.green(),
            "uncommon": discord.Colour.from_rgb(178, 114, 63),
            "rare": discord.Colour.from_rgb(166, 155, 190),
            "very rare": discord.Colour.from_rgb(208, 172, 63),
            "legendary": discord.Colour.from_rgb(140, 194, 216),
            "artifact": discord.Colour.from_rgb(200, 37, 35),
            "varies": discord.Colour.from_rgb(186, 187, 187),
            "unknown": discord.Colour.from_rgb(186, 187, 187),
        }

        color = None
        for type in item.type:
            cleaned_type = type.split("(")[0].strip().lower()
            if cleaned_type in type_colors:
                color = type_colors[cleaned_type]
                break

        self.color = color or discord.Colour.from_rgb(149, 149, 149)
