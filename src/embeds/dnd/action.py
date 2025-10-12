from embeds.dnd.abstract import DNDObjectEmbed
from logic.dnd.action import Action


class ActionEmbed(DNDObjectEmbed):
    def __init__(self, action: Action):
        super().__init__(action)
        self.description = f"*{action.select_description}*"
        self.add_description_fields(action.description)
