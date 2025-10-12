from embeds.dnd.abstract import DNDObjectEmbed
from logic.dnd.background import Background


class BackgroundEmbed(DNDObjectEmbed):
    def __init__(self, background: Background):
        super().__init__(background)
        if background.description:
            self.add_description_fields(background.description)
