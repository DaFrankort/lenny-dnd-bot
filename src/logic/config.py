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
    path: str | None
    server: discord.Guild | None

    def __init__(self, server: discord.Guild | None):
        self.path = None
        self.server = server

        if self.server is not None:
            self.path = f"config/{self.server.id}.config"
            path = pathlib.Path(self.path)
            path.parent.mkdir(exist_ok=True, parents=True)
            open(path, "a").close()  # Ensure file exists

    # region sources

    def get_disallowed_sources(self) -> set[str]:
        if self.path is None:
            return set([*SOURCES_PHB2014])

        config = toml.load(self.path)
        lookup = config.get("lookup", {})
        disallowed = lookup.get("disallowed_sources", None)
        if disallowed is None:
            # 2014 sources are disabled by default
            disallowed = [*SOURCES_PHB2014]
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
    def allowed_sources(server: discord.Guild) -> set[str]:
        return Config(server=server).get_allowed_sources()

    # endregion sources

    # region permissions

    def get_config_roles(self) -> set[int]:
        if self.path is None:
            return set()

        config = toml.load(self.path)
        lookup = config.get("config", {})
        roles = lookup.get("config_roles", None)

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

    # endregion permissions


def user_is_admin(user: discord.User | discord.Member) -> bool:
    return user.guild_permissions.administrator


def user_has_config_permissions(server: discord.Guild | None, user: discord.User | discord.Member) -> bool:
    if server is None:
        return False

    config = Config(server)

    user_role_ids = set([role.id for role in user.roles])
    allowed_role_ids = config.get_config_roles()
    intersection = allowed_role_ids.intersection(user_role_ids)

    # Allow if user has at least one allowed role
    return len(intersection) > 0
