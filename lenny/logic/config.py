from dataclasses import dataclass
from collections.abc import Iterable
import time
from typing import Any

import discord

from logic.dnd.source import SourceList
from logic.jsonhandler import JsonFolderHandler, JsonHandler

# Disallow PHB 2014 sources by default
DEFAULT_DISALLOWED_SOURCES = ["PHB", "DMG", "MM"]

# Words that need to be a substring of the game master role
GAMEMASTER_ROLE_CONTAINING_WORDS = ["game master", "gamemaster", "dungeon master"]

# Words that need to exactly match the game master role
GAMEMASTER_ROLE_EXACT_WORDS = ["gm", "dm"]


@dataclass
class GuildConfig:
    # Lookup
    disallowed_sources: list[str]
    # Permissions
    roles: list[int]

    @classmethod
    def fromdict(cls, obj: Any) -> "GuildConfig":
        return cls(
            disallowed_sources=obj.get("disallowed_sources", DEFAULT_DISALLOWED_SOURCES),
            roles=obj.get("roles", []),
        )


class ConfigHandler(JsonHandler[GuildConfig]):
    guild: discord.Guild

    def __init__(self, guild: discord.Guild):
        super().__init__(str(guild.id), "config")

        self.guild = guild
        if not self.data:
            self.reset()

    @property
    def config(self) -> GuildConfig:
        return self.data["config"]

    @config.setter
    def config(self, new_config: GuildConfig):
        self.data["config"] = new_config

    def reset(self) -> None:
        self.config = GuildConfig(
            disallowed_sources=self.default_disallowed_sources(),
            roles=self.default_config_roles,
        )

    def deserialize(self, obj: Any) -> GuildConfig:
        return GuildConfig.fromdict(obj)

    # region sources

    @staticmethod
    def default_disallowed_sources() -> list[str]:
        # 2014 sources are disabled by default
        return DEFAULT_DISALLOWED_SOURCES

    @property
    def default_allowed_sources(self) -> list[str]:
        source_list = SourceList()
        sources = set(source.id for source in source_list.entries)
        disallowed = set(ConfigHandler.default_disallowed_sources())
        return list(sources - disallowed)

    @property
    def disallowed_sources(self) -> set[str]:
        return set(self.config.disallowed_sources)

    @property
    def allowed_sources(self) -> set[str]:
        source_list = SourceList()
        sources = set(source.id for source in source_list.entries)
        disallowed = self.disallowed_sources
        return sources - disallowed

    def set_disallowed_sources(self, sources: Iterable[str]) -> None:
        self.config.disallowed_sources = list(set(sources))
        self.save()

    def allow_source(self, source: str) -> None:
        disallowed = self.disallowed_sources
        disallowed.discard(source)
        self.set_disallowed_sources(disallowed)

    def disallow_source(self, source: str) -> None:
        disallowed = self.disallowed_sources
        disallowed.add(source)
        self.set_disallowed_sources(disallowed)

    # endregion sources

    # region permissions

    @property
    def allowed_config_roles(self) -> list[int]:
        return self.config.roles

    def set_allowed_config_roles(self, ids: Iterable[int]):
        self.config.roles = list(set(ids))
        self.save()

    @property
    def default_config_roles(self) -> list[int]:
        config_roles: list[int] = []

        # The default allowed roles are those matching the terms game master, dungeon master, dm...
        for role in self.guild.roles:
            role_name = role.name.strip().lower()
            # Check if it exactly matches a game master role
            if role_name in GAMEMASTER_ROLE_EXACT_WORDS:
                config_roles.append(role.id)
            # Check if it is within a partial game master role
            for allowed_name in GAMEMASTER_ROLE_CONTAINING_WORDS:
                if allowed_name in role_name:
                    config_roles.append(role.id)

        return list(set(config_roles))

    def allow_permission(self, role: discord.Role):
        allowed_roles = set(self.allowed_config_roles)
        allowed_roles.add(role.id)
        self.set_allowed_config_roles(allowed_roles)

    def disallow_permission(self, role: discord.Role):
        allowed_roles = self.allowed_config_roles
        allowed_roles.remove(role.id)
        self.set_allowed_config_roles(allowed_roles)

    # endregion permissions

    # region User permissions utilities

    def user_is_admin(self, user: discord.User | discord.Member) -> bool:
        if not isinstance(user, discord.Member):
            return False
        return user.guild_permissions.administrator

    def user_has_config_permissions(self, user: discord.User | discord.Member) -> bool:
        if not isinstance(user, discord.Member):
            return False

        user_role_ids = set(role.id for role in user.roles)
        allowed_role_ids = set(self.allowed_config_roles)
        intersection = allowed_role_ids.intersection(user_role_ids)

        # Allow if user has at least one allowed role
        return len(intersection) > 0

    def user_is_admin_or_has_config_permissions(self, user: discord.User | discord.Member) -> bool:
        return self.user_is_admin(user) or self.user_has_config_permissions(user)


class GlobalConfigHandler(JsonFolderHandler[ConfigHandler]):
    _handler_type = ConfigHandler

    def _itr_key(self, itr: discord.Interaction[discord.Client]) -> int:
        if not itr.guild_id:
            raise RuntimeError("You can only configure settings in a server!")
        return itr.guild_id

    def get(self, itr: discord.Interaction[discord.Client]) -> ConfigHandler:
        # Some of the functionality of ConfigHandler requires the specific guild object
        # (e.g. for managing roles). As such, the guild object needs to be stored inside
        # the handler object. Because `get` only works on the key, and not on the actual
        # interaction, this method needs to be overwritten.

        if not itr.guild:
            raise RuntimeError("You can only configure settings in a server!")

        key = self._itr_key(itr)
        if key not in self._data:
            self._data[key] = ConfigHandler(itr.guild)
        self._last_accessed[key] = int(time.time())
        return self._data[key]


Config = GlobalConfigHandler()
