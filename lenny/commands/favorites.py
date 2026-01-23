import discord
from discord.app_commands import choices

from commands.command import BaseCommand, BaseCommandGroup
from commands.search import item_name_autocomplete, spell_name_autocomplete
from logic.config import Config
from logic.dnd.abstract import DNDEntryType
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

    @choices(filter=DNDEntryType.choices())
    async def handle(self, itr: discord.Interaction, filter: DNDEntryType | None = None):
        self.log(itr)
        if filter is None:
            favorites = FavoritesCache.get(itr).get_all_choices()
        else:
            favorites = FavoritesCache.get(itr).get_choices(filter)

        msg = "**Here are your favorites:**\n- " + "\n- ".join(f.name for f in favorites)
        await itr.response.send_message(msg)


async def dnd_entries_autocomplete(itr: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
    results: list[discord.app_commands.Choice[str]] = []
    autocompletes = [spell_name_autocomplete, item_name_autocomplete]  # TODO Add all in a better way than this.

    for autocomplete in autocompletes:
        results += await autocomplete(itr, current)
        if len(results) > 25:
            break

    return results[:25]


class FavoritesAddCommand(BaseCommand):
    name = "add"
    desc = "Add a favorite D&D Entry"
    help = "Adds a D&D entry to your favorites."

    @discord.app_commands.autocomplete(name=dnd_entries_autocomplete)
    async def handle(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.get(itr).allowed_sources
        entry = Data.search(name, allowed_sources=sources).get_all()[0]  # TODO MATCH SOURCE
        FavoritesCache.get(itr).store(entry)

        await itr.response.send_message(f"Added {entry.title}")


async def favorites_autocomplete(itr: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
    results: list[discord.app_commands.Choice[str]] = []
    favorites = FavoritesCache.get(itr).get_all_choices()
    for favorite in favorites:
        if current.replace(" ", "").lower() in favorite.name.replace(" ", "").lower():
            results.append(favorite)
        if len(results) >= 25:
            break

    return results[:25]


class FavoritesRemoveCommand(BaseCommand):
    name = "remove"
    desc = "Remove an entry from your favorites"
    help = "Removes a D&D entry from your favorites."

    @discord.app_commands.autocomplete(name=favorites_autocomplete)
    async def handle(self, itr: discord.Interaction, name: str):  # type: ignore
        self.log(itr)
        raise NotImplementedError(f"Sorry! I'm still working on this, I can't add your {name}")
