import discord

from logic.dnd.abstract import DNDEntry
from logic.jsonhandler import JsonFolderHandler, JsonHandler


class SearchCacheHandler(JsonHandler[list[str]]):
    def __init__(self, user_id: int):
        super().__init__(str(user_id), "user_search")

    def store(self, entry: DNDEntry):
        value = entry.name.strip()
        key = entry.entry_type
        if key not in self.data:
            self.data[key] = [value]
            return

        if value in self.data[key]:
            self.data[key].remove(value)
        self.data[key].append(value)

        self.data[key] = self.data[key][-5:]
        self.save()

    def get_choices(self, key: str) -> list[discord.app_commands.Choice[str]]:
        if key not in self.data:
            return []
        return [discord.app_commands.Choice(name=value, value=value) for value in reversed(self.data[key])]


class GlobalSearchCache(JsonFolderHandler[SearchCacheHandler]):
    _handler_type = SearchCacheHandler

    def _itr_key(self, itr: discord.Interaction) -> int:
        return itr.user.id


SearchCache = GlobalSearchCache()
