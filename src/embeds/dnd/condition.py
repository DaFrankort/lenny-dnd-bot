from embeds.dnd.abstract import DNDObjectEmbed
from logic.dnd.condition import Condition


class ConditionEmbed(DNDObjectEmbed):
    def __init__(self, condition: Condition):
        super().__init__(condition)

        if len(condition.description) == 0:
            return

        self.description = condition.description[0]["value"]
        self.add_description_fields(condition.description[1:])

        if condition.image:
            self.set_thumbnail(url=condition.image)
