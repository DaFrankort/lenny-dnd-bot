import math
import discord

from components.items import SimpleSeparator
from config import Config
from dnd import DNDData, Source, SourceList
from logger import log_cmd


class ConfigSourcesButton(discord.ui.Button):
    source: Source
    server: discord.Guild
    config: Config
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
        if self.source.id in disallowed:
            self.label = "Disabled"
            self.style = discord.ButtonStyle.red
        else:
            self.label = "‎ Enabled ‎‎"
            self.style = discord.ButtonStyle.green

    async def callback(self, itr: discord.Interaction):
        disallowed = self.config.get_disallowed_sources()
        if self.source.id in disallowed:
            self.config.allow_source(self.source.id)
        else:
            self.config.disallow_source(self.source.id)
        await self.sources_view.rebuild_and_edit(itr)


class ConfigSourcesView(discord.ui.LayoutView):
    page: int  # Page starts counting from 1
    per_page: int
    server: discord.Guild

    def __init__(self, server: discord.Guild):
        super().__init__(timeout=None)
        self.page = 1
        self.per_page = 10
        self.server = server
        self.rebuild()

    def rebuild(self) -> None:
        self.clear_items()
        container = discord.ui.Container(accent_color=discord.Color.dark_green())

        title = "# Enable Sources"
        paging = f"-# Page {self.page}/{self.max_pages}"
        container.add_item(discord.ui.TextDisplay(title))
        container.add_item(discord.ui.TextDisplay(paging))
        container.add_item(SimpleSeparator())

        # Source list
        sources = SourceList()
        sources = sorted(sources.entries, key=lambda s: s.name)
        for source in self.viewed_sources:
            text = discord.ui.TextDisplay(source.name)
            button = ConfigSourcesButton(self, source, self.server)
            container.add_item(discord.ui.Section(text, accessory=button))
        container.add_item(SimpleSeparator())

        # Button navigation
        prev_button = discord.ui.Button(label="⮜")
        prev_button.disabled = self.page <= 1
        prev_button.callback = self.prev_page
        prev_button.style = discord.ButtonStyle.primary

        next_button = discord.ui.Button(label="➤")
        next_button.disabled = self.page >= self.max_pages
        next_button.callback = self.next_page
        next_button.style = discord.ButtonStyle.primary

        row = discord.ui.ActionRow(prev_button, next_button)
        container.add_item(row)

        self.add_item(container)

    @property
    def viewed_sources(self) -> list[Source]:
        sources = SourceList()
        sources = sorted(sources.entries, key=lambda s: s.name)

        start = (self.page - 1) * self.per_page
        end = self.page * self.per_page
        return sources[start:end]

    @property
    def max_pages(self) -> int:
        sources = SourceList()
        return max(int(math.ceil(len(sources.entries) / self.per_page)), 1)

    async def rebuild_and_edit(self, itr: discord.Interaction) -> None:
        self.rebuild()
        await itr.response.edit_message(view=self)

    async def prev_page(self, itr: discord.Interaction) -> None:
        self.page = max(self.page - 1, 1)
        await self.rebuild_and_edit(itr)

    async def next_page(self, itr: discord.Interaction) -> None:
        self.page = min(self.page + 1, self.max_pages)
        await self.rebuild_and_edit(itr)


class ConfigCommand(discord.app_commands.Command):
    name = "config"
    desc = "Configure your server's settings!"
    help = "Open up an overview you can use to configure the bot's settings in your server."
    command = "/config"

    data: DNDData

    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.desc,
            callback=self.callback,
        )

    async def callback(self, itr: discord.Interaction):
        log_cmd(itr)
        view = ConfigSourcesView(server=itr.guild)
        await itr.response.send_message(view=view)
