from embeds.dnd.abstract import DNDObjectEmbed
from logic.dnd.object import DNDObject


class ObjectEmbed(DNDObjectEmbed):
    def __init__(self, obj: DNDObject):
        super().__init__(obj)
        self.description = f"*{obj.select_description}*"
        if obj.token_url:
            self.set_thumbnail(url=obj.token_url)
        self.add_description_fields(obj.description)
