import discord

from components.items import SimpleSeparator
from components.paginated_view import PaginatedLayoutView
from embeds.config.config import ConfigAllowButton
from logic.config import Config, user_is_admin_or_has_config_permissions
from logic.dnd.source import Source, SourceList


class ConfigManageSourcesButton(ConfigAllowButton):
    source: Source
    server: discord.Guild
    config: Config
    sources_view: "ConfigSourcesView"

    def __init__(self, view: "ConfigSourcesView", source: Source, server: discord.Guild, allow_configuration: bool):
        self.source = source
        self.server = server
        self.config = Config(server=self.server)
        self.sources_view = view

        allowed_sources = self.config.get_allowed_sources()

        allowed = self.source.id in allowed_sources
        disabled = not allow_configuration

        super().__init__(allowed=allowed, disabled=disabled)

    async def callback(self, interaction: discord.Interaction):
        if not user_is_admin_or_has_config_permissions(self.server, interaction.user):
            raise PermissionError("You don't have permission to edit sources!")

        if self.allowed:
            self.config.disallow_source(self.source.id)
        else:
            self.config.allow_source(self.source.id)
        await self.sources_view.rebuild(interaction)


class ConfigSourcesView(PaginatedLayoutView):
    allow_configuration: bool
    server: discord.Guild

    def __init__(self, server: discord.Guild, allow_configuration: bool):
        super().__init__()
        self.server = server
        self.allow_configuration = allow_configuration
        self.build()

    def build(self) -> None:
        self.clear_items()
        container = discord.ui.Container[discord.ui.LayoutView](accent_color=discord.Color.dark_green())

        if self.allow_configuration:
            title = "# Manage sources"
        else:
            title = "# View sources\nYou are not allowed to edit sources."
        container.add_item(discord.ui.TextDisplay(title))
        container.add_item(SimpleSeparator())

        # Source list
        sources = SourceList()
        sources = sorted(sources.entries, key=lambda s: s.name)
        for source in self.viewed_sources:
            text = discord.ui.TextDisplay[discord.ui.LayoutView](source.name)
            button = ConfigManageSourcesButton(self, source, self.server, self.allow_configuration)
            container.add_item(discord.ui.Section[discord.ui.LayoutView](text, accessory=button))

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
