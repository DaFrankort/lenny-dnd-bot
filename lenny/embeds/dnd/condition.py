from embeds.dnd.abstract import DNDEntryEmbed
from logic.dnd.condition import Condition


class ConditionEmbed(DNDEntryEmbed):
    def __init__(self, condition: Condition):
        super().__init__(condition)

        if len(condition.description) == 0:
            return

        description = condition.description[0]
        if description["type"] != "text":
            raise ValueError(f"Condition description should be a string, but it is a {description['type']}!")

        self.description = description["value"]
        self.add_description_fields(condition.description[1:])

        if condition.image:
            self.set_thumbnail(url=condition.image)
