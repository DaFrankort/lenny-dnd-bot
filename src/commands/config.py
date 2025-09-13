import discord

from logic.app_commands import SimpleCommand
from components.items import SimpleSeparator
from config import Config
from dnd import DNDData, Source, SourceList
from embed import SimpleEmbed
from components.paginated_view import PaginatedLayoutView


class ConfigSourcesButton(discord.ui.Button):
    source: Source
    server: discord.Guild
    config: Config
    allowed: bool
    sources_view: "ConfigSourcesView"

    def __init__(
        self, view: "ConfigSourcesView", source: Source, server: discord.Guild
    ):
        super().__init__()
        self.source = source
        self.server = server
        self.config = Config(server=self.server)
        self.sources_view = view

        disallowed = self.config.get_disallowed_sources()
        self.allowed = self.source.id not in disallowed

        if self.allowed:
            self.label = "‎ Enabled ‎‎"
            self.style = discord.ButtonStyle.green
        else:
            self.label = "Disabled"
            self.style = discord.ButtonStyle.red

    async def callback(self, itr: discord.Interaction):
        if self.allowed:
            self.config.disallow_source(self.source.id)
        else:
            self.config.allow_source(self.source.id)
        await self.sources_view.rebuild(itr)


class ConfigSourcesView(PaginatedLayoutView):
    server: discord.Guild

    def __init__(self, server: discord.Guild):
        super().__init__()
        self.server = server
        self.build()

    def build(self) -> None:
        self.clear_items()
        container = discord.ui.Container(accent_color=discord.Color.dark_green())

        title = "# Enable Sources"
        container.add_item(discord.ui.TextDisplay(title))
        container.add_item(SimpleSeparator())

        # Source list
        sources = SourceList()
        sources = sorted(sources.entries, key=lambda s: s.name)
        for source in self.viewed_sources:
            text = discord.ui.TextDisplay(source.name)
            button = ConfigSourcesButton(self, source, self.server)
            container.add_item(discord.ui.Section(text, accessory=button))

        # Button navigation
        container.add_item(SimpleSeparator())
        container.add_item(self.navigation_footer())

        self.add_item(container)

    @property
    def entry_count(self) -> int:
        sources = SourceList()
        return len(sources.entries)

    @property
    def viewed_sources(self) -> list[Source]:
        sources = SourceList()
        sources = sorted(sources.entries, key=lambda s: s.name)

        start = self.page * self.per_page
        end = (self.page + 1) * self.per_page
        return sources[start:end]


class ConfigCommand(SimpleCommand):
    name = "config"
    desc = "Configure your server's settings!"
    help = "Open up an overview you can use to configure the bot's settings in your server."

    data: DNDData

    async def callback(self, itr: discord.Interaction):
        self.log(itr)
        if itr.guild is None:
            title = "Cannot change sources!"
            desc = "Sources can only be enabled and disabled in a server."
            await itr.response.send_message(embed=SimpleEmbed(title, desc))
            return

        view = ConfigSourcesView(server=itr.guild)
        await itr.response.send_message(view=view)
