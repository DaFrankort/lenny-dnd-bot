import time
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import discord

from logic.dnd.source import ContentChoice, SourceList
from logic.jsonhandler import JsonFolderHandler, JsonHandler

"""
It is important to note that all official sources (excluding the 2014 sources) are
allowed by default and that all partnered sources are disallowed by default. The 
code is written in such a way that these two are always handled separately when
modifying the config.
"""

OFFICIAL_SOURCES = SourceList(content=ContentChoice.OFFICIAL)
PARTNERED_SOURCES = SourceList(content=ContentChoice.PARTNERED)

# Disallow PHB 2014 sources by default
DEFAULT_DISALLOWED_OFFICIAL_SOURCES = ["PHB", "DMG", "MM"]

# Words that need to be a substring of the game master role
GAMEMASTER_ROLE_CONTAINING_WORDS = ["game master", "gamemaster", "dungeon master"]

# Words that need to exactly match the game master role
GAMEMASTER_ROLE_EXACT_WORDS = ["gm", "dm"]


def is_official_source(source: str) -> bool:
    return OFFICIAL_SOURCES.contains(source)


def is_partnered_source(source: str) -> bool:
    return PARTNERED_SOURCES.contains(source)


@dataclass
class GuildConfig:
    # Lookup
    disallowed_official_sources: list[str]
    allowed_partnered_sources: list[str]

    # Permissions
    roles: list[int]

    @classmethod
    def fromdict(cls, obj: Any) -> "GuildConfig":
        return cls(
            disallowed_official_sources=obj.get("disallowed_official_sources", DEFAULT_DISALLOWED_OFFICIAL_SOURCES),
            allowed_partnered_sources=obj.get("allowed_partnered_sources", []),
            roles=obj.get("roles", []),
        )

    @property
    def allowed_official_sources(self) -> list[str]:
        all_official_sources = set(OFFICIAL_SOURCES.source_ids)
        disallowed_official_sources = set(self.disallowed_official_sources)
        return list(all_official_sources - disallowed_official_sources)

    @property
    def disallowed_partnered_sources(self) -> list[str]:
        all_partnered_sources = set(PARTNERED_SOURCES.source_ids)
        allowed_partnered_sources = set(self.allowed_partnered_sources)
        return list(all_partnered_sources - allowed_partnered_sources)

    @property
    def allowed_sources(self) -> list[str]:
        return [*self.allowed_official_sources, *self.allowed_partnered_sources]

    @property
    def disallowed_sources(self) -> list[str]:
        return [*self.disallowed_official_sources, *self.disallowed_partnered_sources]

    def is_source_allowed(self, source: str) -> bool:
        if is_official_source(source):
            return source in self.allowed_official_sources
        else:
            return source in self.allowed_partnered_sources


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
            disallowed_official_sources=[*DEFAULT_DISALLOWED_OFFICIAL_SOURCES],
            allowed_partnered_sources=[],
            roles=self.default_config_roles,
        )

    def deserialize(self, obj: Any) -> GuildConfig:
        return GuildConfig.fromdict(obj)

    # region sources

    @staticmethod
    def default_disallowed_sources() -> list[str]:
        # 2014 sources are disabled by default
        official_disallowed = DEFAULT_DISALLOWED_OFFICIAL_SOURCES
        # Partnered sources are disallowed by default
        partnered_disallowed = list(PARTNERED_SOURCES.source_ids)
        return [*official_disallowed, *partnered_disallowed]

    @property
    def disallowed_sources(self) -> set[str]:
        return set(self.config.disallowed_sources)

    @property
    def allowed_sources(self) -> set[str]:
        return set(self.config.allowed_sources)

    def set_disallowed_sources(self, sources: Iterable[str]) -> None:
        official_sources = [source for source in sources if is_official_source(source)]
        partnered_sources = [source for source in sources if is_partnered_source(source)]

        disallowed_official_sources = set(self.config.disallowed_official_sources + official_sources)
        allowed_partnered_sources = set(self.config.allowed_partnered_sources) - set(partnered_sources)

        self.config.disallowed_official_sources = list(disallowed_official_sources)
        self.config.allowed_partnered_sources = list(allowed_partnered_sources)

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
