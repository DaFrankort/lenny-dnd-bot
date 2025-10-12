from embeds.dnd.abstract import HORIZONTAL_LINE, DNDObjectEmbed
from logic.dnd.feat import Feat


class FeatEmbed(DNDObjectEmbed):
    def __init__(self, feat: Feat):
        super().__init__(feat)
        self.description = f"*{feat.select_description}*"

        if feat.ability_increase:
            self.add_field(name="Ability Increase", value=feat.ability_increase, inline=True)
        if feat.prerequisite:
            self.add_field(name="Requires", value=feat.prerequisite, inline=True)
        if feat.ability_increase or feat.prerequisite:
            self.add_field(name="", value=HORIZONTAL_LINE, inline=False)

        self.add_description_fields(feat.description)
