from embeds.dnd.abstract import DNDEntryEmbed
from logic.dnd.optionalfeature import OptionalFeature


class OptionalFeatureEmbed(DNDEntryEmbed):

    def __init__(self, optional_feat: OptionalFeature):
        super().__init__(entry=optional_feat)

        if optional_feat.prerequisite:
            self.add_field(name="Prerequisite", value=optional_feat.prerequisite, inline=True)
        self.add_field(name="Type", value=optional_feat.type, inline=True)
        self.add_description_fields(optional_feat.description)
