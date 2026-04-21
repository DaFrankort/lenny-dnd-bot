import discord

from embeds.embed import BaseEmbed
from logic.average import AverageDamageResults
from logic.color import UserColor
from logic.dnd.abstract import build_table_from_rows


class AverageDamageEmbed(BaseEmbed):
    results: AverageDamageResults

    def __init__(self, itr: discord.Interaction, results: AverageDamageResults):
        self.results = results
        super().__init__("Your averages", None, discord.Color(UserColor.get(itr)))

        self.description = self.get_table()

    def get_table(self):
        acs = self.results.acs
        advantages = self.results.advantages

        headers = ["AC", *[str(adv).capitalize() for adv in advantages]]
        rows = [(str(ac), *[self.results.get(ac, adv) for adv in advantages]) for ac in acs]

        return build_table_from_rows(headers, rows, align_right=True)
