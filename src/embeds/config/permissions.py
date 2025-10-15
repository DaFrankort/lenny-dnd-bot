from typing import Literal
import discord

from components.items import SimpleSeparator
from components.paginated_view import PaginatedLayoutView
from logic.config import Config


class ConfigManagePermissionsButton(discord.ui.Button):
    role: discord.Role | Literal["admin"]
    server: discord.Guild
    config: Config
    permissions_view: "ConfigPermissionsView"
    allowed: bool

    def __init__(
        self,
        view: "ConfigPermissionsView",
        role: discord.Role | Literal["admin"],
        server: discord.Guild,
    ):
        super().__init__()
        self.role = role
        self.server = server
        self.config = Config(server=self.server)
        self.permissions_view = view

        self.allowed = (self.role == "admin") or (self.role.id in self.config.get_allowed_config_roles())

        if self.allowed:
            self.label = "‎ Enabled ‎‎"
            self.style = discord.ButtonStyle.green
        else:
            self.label = "Disabled"
            self.style = discord.ButtonStyle.red

        # Note: this is disallowing the pressing of the button, only the admin role can't be changed
        self.disabled = self.role == "admin"

    async def callback(self, itr: discord.Interaction):
        if self.role == "admin":
            pass  # Disallow removing admin permission
        elif self.allowed:
            self.config.disallow_permission(self.role)
        else:
            self.config.allow_permission(self.role)
        await self.permissions_view.rebuild(itr)


class ConfigPermissionsView(PaginatedLayoutView):
    server: discord.Guild

    def __init__(self, server: discord.Guild):
        super().__init__()
        self.server = server
        self.build()

    def build(self) -> None:
        self.clear_items()
        container = discord.ui.Container(accent_color=discord.Color.dark_green())

        title = "# Manage Permissions"
        container.add_item(discord.ui.TextDisplay(title))
        container.add_item(SimpleSeparator())

        roles = self.viewed_permissions
        for role in roles:
            text = "Admin (cannot be changed)" if role == "admin" else f"{role.name}"
            button = ConfigManagePermissionsButton(self, role, self.server)
            container.add_item(discord.ui.Section(text, accessory=button))

        # Button navigation
        container.add_item(SimpleSeparator())
        container.add_item(self.navigation_footer())

        self.add_item(container)

    @property
    def entry_count(self) -> int:
        return len(self.server.roles) + 1  # Include one for admin

    @property
    def viewed_permissions(self) -> list[discord.Role | Literal["admin"]]:
        roles = reversed(self.server.roles)  # Prioritize higher roles
        roles = ["admin", *roles]

        start = self.page * self.per_page
        end = (self.page + 1) * self.per_page
        return roles[start:end]
