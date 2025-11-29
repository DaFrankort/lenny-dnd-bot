from typing import Literal

import discord

from components.items import SimpleSeparator
from components.paginated_view import PaginatedLayoutView
from embeds.config.config import ConfigAllowButton
from logic.config import Config


class ConfigManagePermissionsButton(ConfigAllowButton):
    role: discord.Role | Literal["admin"]
    guild: discord.Guild
    permissions_view: "ConfigPermissionsView"

    def __init__(self, view: "ConfigPermissionsView", role: discord.Role | Literal["admin"], itr: discord.Interaction):
        self.role = role
        self.permissions_view = view

        config = Config.get(itr)
        allowed = (self.role == "admin") or (self.role.id in config.allowed_config_roles)
        # Note: this is disallowing the pressing of the button, only the admin role can't be changed
        disabled = self.role == "admin"

        super().__init__(allowed=allowed, disabled=disabled)

    async def callback(self, interaction: discord.Interaction):
        config = Config.get(interaction)
        if not config.user_is_admin(interaction.user):
            raise PermissionError("Only admins can change permissions!")

        if self.role == "admin":
            pass  # Disallow removing admin permission
        elif self.allowed:
            config.disallow_permission(self.role)
        else:
            config.allow_permission(self.role)
        await self.permissions_view.rebuild(interaction)


class ConfigPermissionsView(PaginatedLayoutView):
    itr: discord.Interaction

    def __init__(self, itr: discord.Interaction):
        super().__init__()
        self.itr = itr
        self.build()

    def build(self) -> None:
        self.clear_items()
        container = discord.ui.Container[ConfigPermissionsView](accent_color=discord.Color.dark_green())

        title = "# Manage Permissions"
        container.add_item(discord.ui.TextDisplay(title))
        container.add_item(SimpleSeparator())

        roles = self.viewed_permissions
        for role in roles:
            text = "Admin (cannot be changed)" if role == "admin" else role.name
            button = ConfigManagePermissionsButton(self, role, self.itr)
            container.add_item(discord.ui.Section(text, accessory=button))

        # Button navigation
        container.add_item(SimpleSeparator())
        container.add_item(self.navigation_footer())

        self.add_item(container)

    @property
    def entry_count(self) -> int:
        if not self.itr.guild:
            return 1
        return len(self.itr.guild.roles) + 1  # Include one for admin

    @property
    def viewed_permissions(self) -> list[discord.Role | Literal["admin"]]:
        if not self.itr.guild:
            roles = ["admin"]
        else:
            roles: list[discord.Role | Literal["admin"]] = ["admin", *reversed(self.itr.guild.roles)]  # Prioritize higher roles

        start = self.page * self.per_page
        end = (self.page + 1) * self.per_page
        return roles[start:end]
