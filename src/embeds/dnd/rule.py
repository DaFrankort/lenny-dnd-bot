from embeds.dnd.abstract import DNDEntryEmbed
from logic.dnd.rule import Rule


class RuleEmbed(DNDEntryEmbed):
    def __init__(self, rule: Rule):
        super().__init__(rule)
        self.description = f"*{rule.select_description}*"
        self.add_description_fields(rule.description)
