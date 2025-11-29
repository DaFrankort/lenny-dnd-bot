import discord

from components.items import SimpleSeparator
from components.paginated_view import PaginatedLayoutView
from embeds.config.config import ConfigAllowButton
from logic.config import Config
from logic.dnd.source import Source, SourceList


class ConfigManageSourcesButton(ConfigAllowButton):
    source: Source
    guild: discord.Guild
    sources_view: "ConfigSourcesView"

    def __init__(self, view: "ConfigSourcesView", itr: discord.Interaction, source: Source, allow_configuration: bool):
        self.source = source
        self.sources_view = view

        config = Config.get(itr)
        allowed_sources = config.allowed_sources

        allowed = self.source.id in allowed_sources
        disabled = not allow_configuration

        super().__init__(allowed=allowed, disabled=disabled)

    async def callback(self, interaction: discord.Interaction):
        config = Config.get(interaction)
        if not config.user_is_admin_or_has_config_permissions(interaction.user):
            raise PermissionError("You don't have permission to edit sources!")

        if self.allowed:
            config.disallow_source(self.source.id)
        else:
            config.allow_source(self.source.id)
        await self.sources_view.rebuild(interaction)


class ConfigSourcesView(PaginatedLayoutView):
    allow_configuration: bool
    itr: discord.Interaction

    def __init__(self, itr: discord.Interaction, allow_configuration: bool):
        super().__init__()
        self.itr = itr
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
            button = ConfigManageSourcesButton(self, self.itr, source, self.allow_configuration)
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
