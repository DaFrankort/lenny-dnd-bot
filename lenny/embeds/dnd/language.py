from embeds.dnd.abstract import HORIZONTAL_LINE, DNDEntryEmbed
from logic.dnd.language import Language


class LanguageEmbed(DNDEntryEmbed):
    def __init__(self, language: Language):
        super().__init__(language)
        self.description = f"*{language.select_description}*"

        if language.speakers:
            self.add_field(name="Typical Speakers", value=language.speakers, inline=True)
        if language.script:
            self.add_field(name="Script", value=language.script, inline=True)

        if language.description:
            if len(self.fields) > 0:
                self.add_field(name="", value=HORIZONTAL_LINE, inline=False)
            self.add_description_fields(language.description)
