import discord
from discord.app_commands import choices

from commands.command import BaseCommand
from logic.dnd.abstract import DNDEntryType
from logic.favorites import FavoritesCache


class FavoritesCommand(BaseCommand):
    name = "favorites"
    desc = "Manage your favorite D&D entries"
    help = "Manage and view your favorite D&D entries."

    @choices(filter=DNDEntryType.choices())
    async def handle(self, itr: discord.Interaction, filter: DNDEntryType | None = None):
        self.log(itr)
        if filter is None:
            favorites = FavoritesCache.get(itr).get_all_choices()
        else:
            favorites = FavoritesCache.get(itr).get_choices(filter)

        msg = "**Here are your favorites:**\n- " + "\n- ".join(f.name for f in favorites)
        await itr.response.send_message(msg)
