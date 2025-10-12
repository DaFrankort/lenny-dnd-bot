from embeds.dnd.abstract import DNDObjectEmbed
from logic.dnd.creature import Creature


class CreatureEmbed(DNDObjectEmbed):
    def __init__(self, creature: Creature):
        super().__init__(creature)
        self.description = creature.subtitle

        if creature.token_url:
            self.set_thumbnail(url=creature.token_url)

        if creature.summoned_by_spell:
            self.add_field(name="Summoned by:", value=creature.summoned_by_spell)

        if creature.description:
            self.add_description_fields(
                creature.description, ignore_tables=True, MAX_FIELDS=3
            )
