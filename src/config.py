from typing import Iterable
import discord
import pathlib
import toml

from dnd import SourceList


SOURCES_PHB2014 = ["PHB", "DMG", "MM"]


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
