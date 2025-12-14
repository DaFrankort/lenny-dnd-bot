from embeds.dnd.abstract import DNDEntryEmbed
from logic.dnd.deities import Deity


class DeityEmbed(DNDEntryEmbed):
    def __init__(self, deity: Deity):
        super().__init__(entry=deity, thumbnail_url=deity.symbol_url)
        self.description = f"*{deity.select_description}*"

        # Ensure inline fields are 3 per line, for styling.
        inline_fields = deity.inline_desc
        render_inline = len(inline_fields) >= 3
        if render_inline:
            padding_count = len(inline_fields) % 3
            for _ in range(padding_count):
                inline_fields.append({"name": "", "type": "text", "value": ""})
        for field in inline_fields:
            self.add_field(name=field["name"], value=field["value"], inline=render_inline)

        if deity.description:
            self.add_separator_field()
            self.add_description_fields(deity.description)
