import discord

from logic.dnd.abstract import DNDEntry
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
            raise ValueError(f"``{entry.title}`` is already in your favorites!")

        # TODO: Not source specific yet, e.g. if a player favorites Barbarian, it could constantly prompt them if they want PHB or XPHB barbarian.
        self.data[key].append(entry.title)  # TODO: Do we want a limit?
        self.data[key] = sorted(self.data[key])
        self.save()

    def delete(self, name_to_delete: str):
        target_key: str | None = None
        for key, names in self.data.items():
            for name in names:
                if name_to_delete == name:
                    target_key = key
                    break

        if target_key is None:
            raise ValueError(f"``{name_to_delete}`` is not in your favorites, failed to remove!")

        self.data[target_key].remove(name_to_delete)
        self.save()

    def get(self, key: str) -> list[str]:
        if key not in self.data:
            return []
        return self.data[key]

    def get_all(self) -> list[str]:
        data: list[str] = []
        for key in self.data:
            data += self.get(key)
        return data

    def get_choices(self, key: str) -> list[discord.app_commands.Choice[str]]:
        return [discord.app_commands.Choice(name=f"★ {value}", value=value) for value in self.get(key)]

    def get_all_choices(self) -> list[discord.app_commands.Choice[str]]:
        choices: list[discord.app_commands.Choice[str]] = []
        for key in self.data:
            choices += self.get_choices(key)
        return choices


class GlobalFavoritesHandler(JsonFolderHandler[FavoritesHandler]):
    _handler_type = FavoritesHandler

    def _itr_key(self, itr: discord.Interaction) -> int:
        return itr.user.id


FavoritesCache = GlobalFavoritesHandler()
