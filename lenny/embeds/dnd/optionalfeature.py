from embeds.dnd.abstract import HORIZONTAL_LINE, DNDEntryEmbed
from logic.dnd.optionalfeature import OptionalFeature


class OptionalFeatureEmbed(DNDEntryEmbed):

    def __init__(self, optional_feat: OptionalFeature):
        super().__init__(entry=optional_feat)
        self.description = f"*{optional_feat.type}*"

        if optional_feat.prerequisite:
            self.add_field(name="Requires", value=optional_feat.prerequisite)
        if len(optional_feat.description) > 0:
            self.add_field(name="", value=HORIZONTAL_LINE, inline=False)
            self.add_description_fields(optional_feat.description)
