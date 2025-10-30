import os
from typing import Iterable
import discord
import pathlib
import toml

from logic.dnd.source import SourceList


SOURCES_PHB2014 = ["PHB", "DMG", "MM"]

# Words that need to be a substring of the game master role
GAMEMASTER_ROLE_CONTAINING_WORDS = ["game master", "gamemaster", "dungeon master"]

# Words that need to exactly match the game master role
GAMEMASTER_ROLE_EXACT_WORDS = ["gm", "dm"]


def is_source_phb2014(source: str) -> bool:
    return source in SOURCES_PHB2014


class Config(object):
    server: discord.Guild

    def __init__(self, server: discord.Guild | None):
        if server is None:
            raise RuntimeError("You can only configure settings in a server!")

        self.server = server
        self.create_file()

    @property
    def path(self) -> str:
        return f"config/{self.server.id}.config"

    def create_file(self):
        """Creates the associated config file. Does not change anything if it already exists."""
        if self.path is not None:
            path = pathlib.Path(self.path)
            path.parent.mkdir(exist_ok=True, parents=True)
            open(path, "a").close()  # Ensure file exists

    def reset(self):
        if os.path.exists(self.path):
            os.remove(self.path)
            self.create_file()

    # region sources
    @classmethod
    def get_default_disallowed_sources(cls) -> set[str]:
        # 2014 sources are disabled by default
        return set(SOURCES_PHB2014)

    @classmethod
    def get_default_allowed_sources(cls) -> set[str]:
        sources = SourceList()
        sources = set([source.id for source in sources.entries])
        disallowed = cls.get_default_disallowed_sources()
        return sources - disallowed

    def get_disallowed_sources(self) -> set[str]:
        if self.path is None:
            return set([*SOURCES_PHB2014])

        config = toml.load(self.path)
        lookup = config.get("lookup", {})
        disallowed = lookup.get("disallowed_sources", None)
        if disallowed is None:
            return self.get_default_disallowed_sources()
        return set(disallowed)

    def get_allowed_sources(self) -> set[str]:
        sources = SourceList()
        sources = set([source.id for source in sources.entries])
        disallowed = self.get_disallowed_sources()
        return sources - disallowed

    def set_disallowed_sources(self, sources: Iterable[str]) -> None:
        config = toml.load(self.path)
        config["lookup"] = config.get("lookup", {})
        config["lookup"]["disallowed_sources"] = list(set(sources))
        with open(self.path, "w") as f:
            toml.dump(config, f)

    def allow_source(self, source: str) -> None:
        disallowed = self.get_disallowed_sources()
        disallowed.discard(source)
        self.set_disallowed_sources(disallowed)

    def disallow_source(self, source: str) -> None:
        disallowed = self.get_disallowed_sources()
        disallowed.add(source)
        self.set_disallowed_sources(disallowed)

    def clear(self) -> None:
        # Clear config file contents
        open(self.path, "w").close()

    @staticmethod
    def allowed_sources(server: discord.Guild | None) -> set[str]:
        if server is None:
            return Config.get_default_disallowed_sources()
        return Config(server=server).get_allowed_sources()

    # endregion sources

    # region permissions

    def set_allowed_config_roles(self, ids: set[int]):
        config = toml.load(self.path)
        config["permissions"] = config.get("permissions", {})
        config["permissions"]["roles"] = list(set(ids))
        with open(self.path, "w") as f:
            toml.dump(config, f)

    def get_allowed_config_roles(self) -> set[int]:
        if self.path is None:
            return set()

        config = toml.load(self.path)
        lookup = config.get("permissions", {})
        roles = lookup.get("roles", None)

        # If config sources is none, it means they aren't configured yet.
        # In this case, fall back on the server's default roles.
        if roles is None:
            return self.get_default_config_roles()

        return set(roles)

    def get_default_config_roles(self) -> set[int]:
        if self.server is None:
            return set()

        config_roles = []

        # The default allowed roles are those matching the terms game master, dungeon master, dm...
        for role in self.server.roles:
            role_name = role.name.strip().lower()
            # Check if it exactly matches a game master role
            if role_name in GAMEMASTER_ROLE_EXACT_WORDS:
                config_roles.append(role.id)
            # Check if it is within a partial game master role
            for allowed_name in GAMEMASTER_ROLE_CONTAINING_WORDS:
                if allowed_name in role_name:
                    config_roles.append(role.id)

        return set(config_roles)

    def allow_permission(self, role: discord.Role):
        allowed_roles = self.get_allowed_config_roles()
        allowed_roles.add(role.id)
        self.set_allowed_config_roles(allowed_roles)

    def disallow_permission(self, role: discord.Role):
        allowed_roles = self.get_allowed_config_roles()
        allowed_roles.remove(role.id)
        self.set_allowed_config_roles(allowed_roles)

    # endregion permissions


def user_is_admin(user: discord.User | discord.Member) -> bool:
    if not isinstance(user, discord.Member):
        return False
    return user.guild_permissions.administrator


def user_has_config_permissions(server: discord.Guild | None, user: discord.User | discord.Member) -> bool:
    if server is None:
        return False

    if not isinstance(user, discord.Member):
        return False

    config = Config(server)

    user_role_ids = set([role.id for role in user.roles])
    allowed_role_ids = config.get_allowed_config_roles()
    intersection = allowed_role_ids.intersection(user_role_ids)

    # Allow if user has at least one allowed role
    return len(intersection) > 0


def user_is_admin_or_has_config_permissions(server: discord.Guild | None, user: discord.User | discord.Member) -> bool:
    return user_is_admin(user) or user_has_config_permissions(server, user)
