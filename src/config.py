from typing import Iterable
import discord
import pathlib
import toml

from dnd import SourceList


SOURCES_PHB2014 = ["PHB", "DMG", "MM"]


def is_source_phb2014(source: str) -> bool:
    return source in SOURCES_PHB2014


class Config(object):
    server: discord.Guild

    def __init__(self, server: discord.Guild):
        self.server = server
        self.verify_path()

    def verify_path(self) -> None:
        path = pathlib.Path(self.path)
        path.parent.mkdir(exist_ok=True, parents=True)
        with open(path, "a") as f:
            f.write("")

    @property
    def path(self) -> str:
        return f"config/{self.server.id}.config"

    def get_disallowed_sources(self) -> set[str]:
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
        open(self.path, 'w').close()

    @staticmethod
    def allowed_sources(server: discord.Guild) -> set[str]:
        return Config(server=server).get_allowed_sources()
