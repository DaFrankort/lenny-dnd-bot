import dataclasses
import logging
import os
from typing import Any, Set

import discord
from discord.app_commands import Choice

from logic.jsonhandler import JsonHandler

PROFILE_PATH: str = "./temp/profiles/"


@dataclasses.dataclass
class ProfileEntry(object):
    name: str
    img_url: str | None
    is_active: bool

    @classmethod
    def fromdict(cls, data: Any) -> "ProfileEntry":
        return cls(name=data["name"], img_url=data.get("img_url", None), is_active=data["is_active"])


class UserProfileData(JsonHandler[list[ProfileEntry]]):
    user_id: int
    KEY = "profiles"
    active_index: int
    profile_limit: int = 6

    def __init__(self, user_id: int):
        self.user_id = user_id
        super().__init__(filename=str(user_id), sub_dir="profiles")
        self._init_active_index()

    @property
    def profiles(self) -> list[ProfileEntry]:
        return self.data[self.KEY]

    def deserialize(self, obj: Any) -> list[ProfileEntry]:
        return [ProfileEntry.fromdict(o) for o in obj]

    def _find(self, name: str) -> tuple[int, ProfileEntry] | tuple[None, None]:
        for index, profile in enumerate(self.profiles):
            if name.lower() != profile.name.lower():
                continue
            return index, profile
        return None, None

    def _init_active_index(self):
        """Initializes the active_index and clears up any invalid data."""
        active_indexes: list[int] = []
        for i, profile in enumerate(self.profiles):
            if profile.is_active:
                active_indexes.append(i)

        length = len(active_indexes)
        if length == 0:
            self.active_index = 0
            self.data[self.KEY][self.active_index].is_active = True
            self.save()
            return

        if length == 1:
            self.active_index = active_indexes[0]
            return

        self.active_index = active_indexes.pop()
        for index in active_indexes:
            self.data[self.KEY][index].is_active = False
        self.save()

    def add(self, name: str) -> ProfileEntry:
        if self._find(name):
            raise ValueError(f"A profile with the name ``{name}`` already exists!")

        if len(self.profiles) > self.profile_limit:
            raise ValueError(
                f"You have exceeded the max. amount of profiles ({self.profile_limit})\nPlease remove or edit an existing one instead."
            )

        new_entry = ProfileEntry(name=name, img_url=None, is_active=False)
        self.data[self.KEY].append(new_entry)
        self.save()
        return new_entry

    def delete(self, name: str) -> ProfileEntry:
        delete_index, _ = self._find(name)
        if delete_index is None:
            raise ValueError(f"Could not delete profile ``{name}``, profile does not exist.")
        deleted = self.profiles.pop(delete_index)
        self.save()
        return deleted

    def edit(self, entry_name: str, new_name: str | None, new_img_url: str | None) -> ProfileEntry:
        edit_index, entry = self._find(entry_name)
        if edit_index is None or entry is None:
            raise ValueError(f"Could not edit profile ``{entry_name}``, profile does not exist.")
        entry.name = new_name or entry.name
        entry.img_url = new_img_url or entry.img_url

        self.data[self.KEY][edit_index] = entry
        self.save()
        return entry

    async def activate_profile(self, itr: discord.Interaction, name: str) -> ProfileEntry:
        index, entry = self._find(name)
        if index is None or entry is None:
            raise ValueError(f"Could not activate profile ``{name}``, profile does not exist.")

        self.data[self.KEY][self.active_index].is_active = False
        self.active_index = index
        self.data[self.KEY][self.active_index].is_active = True
        self.save()

        if itr.permissions and itr.permissions.manage_nicknames:
            try:
                await itr.user.edit(nick=entry.name)  # type: ignore
            except Exception:
                ...
        return entry

    def get(self, entry_name: str) -> ProfileEntry:
        _, entry = self._find(entry_name)
        if entry is None:
            raise ValueError(f"No profile with the name ``{entry_name}`` found!")
        return entry

    def get_active(self, itr: discord.Interaction) -> ProfileEntry:
        if len(self.profiles) == 0:
            self.add(itr.user.display_name)  # Create default profile

        max_index = len(self.profiles) - 1
        if self.active_index > max_index:
            self._init_active_index()

        return self.profiles[self.active_index]

    def get_autocomplete_suggestions(
        self,
        itr: discord.Interaction,
        query: str,
        fuzzy_threshold: float = 75,
        limit: int = 25,
    ) -> list[Choice[str]]: ...


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
        if itr.user.id not in self._data:
            self._data[itr.user.id] = UserProfileData(itr.user.id)
        return self._data[itr.user.id]

    @property
    def guilds(self) -> Set[int]:
        return set(self._data.keys())


ProfileData = GlobalProfileData()
