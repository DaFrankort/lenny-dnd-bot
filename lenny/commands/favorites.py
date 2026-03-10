import discord
from discord.app_commands import choices

from commands.command import BaseCommand, BaseCommandGroup
from embeds.embed import BaseEmbed
from embeds.favorites import FavoriteAddedEmbed, FavoritesLayoutView
from logic.config import Config
from logic.dnd.abstract import DNDEntryType, fuzzy_matches_list
from logic.dnd.data import Data
from logic.favorites import FavoritesCache


class FavoritesCommandGroup(BaseCommandGroup):
    name = "favorites"
    desc = "Manage your favorite D&D entries."

    def __init__(self):
        super().__init__()
        self.add_command(FavoritesViewCommand())
        self.add_command(FavoritesAddCommand())
        self.add_command(FavoritesRemoveCommand())


class FavoritesViewCommand(BaseCommand):
    name = "view"
    desc = "Manage your favorite D&D entries"
    help = "Manage and view your favorite D&D entries."

    @choices(type_filter=DNDEntryType.choices())
    async def handle(self, itr: discord.Interaction, type_filter: DNDEntryType | None = None):
        if type_filter is None:
            favorites = FavoritesCache.get(itr).get_all()
        else:
            favorites = FavoritesCache.get(itr).get(type_filter)

        view = FavoritesLayoutView(favorites)
        await itr.response.send_message(view=view, ephemeral=True)


async def dnd_entries_autocomplete(itr: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
    if current.strip() == "":
        return []
    sources = Config.get(itr).allowed_sources
    entries = Data.search(current, sources)
    results: list[discord.app_commands.Choice[str]] = []

    for entry in entries.get_all_sorted():
        results.append(discord.app_commands.Choice(name=entry.title, value=entry.title))
        if len(results) > 25:
            break

    return results[:25][::-1]


class FavoritesAddCommand(BaseCommand):
    name = "add"
    desc = "Add a favorite D&D Entry"
    help = "Adds a D&D entry to your favorites."

    @discord.app_commands.autocomplete(name=dnd_entries_autocomplete)
    async def handle(self, itr: discord.Interaction, name: str):
        sources = Config.get(itr).allowed_sources
        entries = Data.search(name, sources, 95).get_all()
        for entry in entries:
            if entry.title == name:
                FavoritesCache.get(itr).store(entry)
                await itr.response.send_message(embed=FavoriteAddedEmbed(entry), ephemeral=True)
                return
        raise KeyError(f"Could not find {name}")


async def favorites_autocomplete(itr: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
    favorites = FavoritesCache.get(itr).get_all()
    return [match.choice for match in fuzzy_matches_list(current, favorites)][:25]


class FavoritesRemoveCommand(BaseCommand):
    name = "remove"
    desc = "Remove an entry from your favorites"
    help = "Removes a D&D entry from your favorites."

    @discord.app_commands.autocomplete(name=favorites_autocomplete)
    async def handle(self, itr: discord.Interaction, name: str):
        FavoritesCache.get(itr).delete(name_to_delete=name)
        embed = BaseEmbed(title="Removed favorite!", description=f"``{name}`` was **removed** from your favorites.")
        await itr.response.send_message(embed=embed, ephemeral=True)
