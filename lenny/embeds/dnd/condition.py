from embeds.dnd.abstract import DNDEntryEmbed
from logic.dnd.condition import Condition


class ConditionEmbed(DNDEntryEmbed):
    def __init__(self, condition: Condition):
        super().__init__(condition)

        if condition.image:
            self.set_thumbnail(url=condition.image)

        if len(condition.description) != 0:
            self.add_description_fields(condition.description)
