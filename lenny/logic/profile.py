import dataclasses
import logging
import os
from typing import Any, Set

import discord
from discord.app_commands import Choice
from jsonhandler import JsonHandler

PROFILE_PATH: str = "./temp/profiles/"


@dataclasses.dataclass
class ProfileEntry(object):
    name: str
    img_url: str | None

    @classmethod
    def fromdict(cls, data: Any) -> "ProfileEntry":
        return cls(name=data["name"], img_url=data.get("img_url", None))


class UserProfileData(JsonHandler[list[ProfileEntry]]):
    user_id: int
    KEY = "data"

    def __init__(self, user_id: int):
        self.user_id = user_id
        super().__init__(filename=str(user_id), sub_dir="profiles")

    def deserialize(self, obj: Any) -> list[ProfileEntry]:
        return [ProfileEntry.fromdict(o) for o in obj]

    def _find(self, name: str) -> ProfileEntry | None:
        for _, items in self.data.items():
            for item in items:
                if name.lower() != item.name.lower():
                    continue
                return item
        return None

    def add(self, itr: discord.Interaction, name: str) -> ProfileEntry:
        if self._find(name):
            raise ValueError(f"A profile with the name '{name}' already exists!")

        new_entry = ProfileEntry(name=name, img_url=None)
        self.data[self.KEY].append(new_entry)
        self.save()
        return new_entry

    def delete(self, itr: discord.Interaction, name: str) -> ProfileEntry:
        entry_to_delete = self._find(name)
        if entry_to_delete is None:
            raise ValueError(f"Could not delete profile '{name}', profile does not exist.")

        self.data[self.KEY].remove(entry_to_delete)
        self.save()
        return entry_to_delete

    def edit(self, itr: discord.Interaction, entry: ProfileEntry, name: str, img_url: str) -> ProfileEntry:
        edited_entry = ProfileEntry(name=name, img_url=img_url)
        self.data[self.KEY].remove(entry)
        self.data[self.KEY].append(edited_entry)
        self.save()
        return edited_entry

    def get(self, entry_name: str) -> ProfileEntry:
        entry = self._find(entry_name)
        if entry is None:
            raise ValueError(f"No homebrew entry with the name '{entry_name}' found!")
        return entry

    def get_all(self) -> list[ProfileEntry]:
        entries: list[ProfileEntry] = []
        for _, items in self.data.items():
            entries.extend(items)
        return entries

    def get_autocomplete_suggestions(
        self,
        itr: discord.Interaction,
        query: str,
        fuzzy_threshold: float = 75,
        limit: int = 25,
    ) -> list[Choice[str]]:
        return []


class GlobalProfileData:
    _data: dict[int, UserProfileData] = {}

    def __init__(self):
        if not os.path.exists(PROFILE_PATH):
            os.makedirs(PROFILE_PATH)
            logging.info(f"Created profile directory at '{PROFILE_PATH}'")
            return

        for filename in os.listdir(PROFILE_PATH):
            if not filename.endswith(".json"):
                continue
            user_id = int(filename[:-5])
            self._data[user_id] = UserProfileData(user_id)

    def get(self, itr: discord.Interaction) -> UserProfileData:
        if not itr.user:
            raise ValueError("Interaction must be done by a user!")
        if itr.user.id not in self._data:
            self._data[itr.user.id] = UserProfileData(itr.user.id)
        return self._data[itr.user.id]

    @property
    def guilds(self) -> Set[int]:
        return set(self._data.keys())


ProfileData = GlobalProfileData()
