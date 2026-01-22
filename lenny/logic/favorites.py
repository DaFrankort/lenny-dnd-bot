import discord

from logic.dnd.abstract import DNDEntry, DNDEntryType
from logic.jsonhandler import JsonFolderHandler, JsonHandler


class FavoritesHandler(JsonHandler[list[str]]):
    def __init__(self, user_id: int):
        super().__init__(filename=str(user_id), sub_dir="user_favorites")

    def store(self, entry: DNDEntry):
        value = entry.title.strip()
        key = entry.entry_type
        if key not in self.data:
            self.data[key] = []

        if value in self.data[key]:
            raise ValueError(f"``{entry.name}`` is already in your favorites!")
        # TODO: Not source specific yet, e.g. if a player favorites Barbarian, it could constantly prompt them if they want PHB or XPHB barbarian.
        self.data[key].append(entry.name)
        # TODO: Do we want a limit?
        self.data[key] = sorted(self.data[key])
        self.save()

    def get_choices(self, key: str) -> list[discord.app_commands.Choice[str]]:
        if key not in self.data:
            return []
        return [discord.app_commands.Choice(name=f"★ {value}", value=value) for value in self.data[key]]

    def get_all_choices(self) -> list[discord.app_commands.Choice[str]]:
        choices: list[discord.app_commands.Choice[str]] = []
        for key in DNDEntryType.values():
            choices += self.get_choices(key)
        return choices


class GlobalFavoritesHandler(JsonFolderHandler[FavoritesHandler]):
    _handler_type = FavoritesHandler

    def _itr_key(self, itr: discord.Interaction) -> int:
        return itr.user.id


FavoritesCache = GlobalFavoritesHandler()
