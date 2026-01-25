import discord

from logic.color import UserColor


class BaseEmbed(discord.Embed):
    def __init__(self, title: str, description: str | None, color: discord.Color | None = None) -> None:
        color = color or discord.Color.dark_green()

        super().__init__(color=color, title=title, type="rich", url=None, description=None, timestamp=None)

        if description:
            self.add_field(name="", value=description, inline=False)


class SuccessEmbed(BaseEmbed):
    """A class based on BaseEmbed to easily toggle the color from green to red."""

    def __init__(self, title_success: str, title_fail: str, description: str | None, success: bool):
        title = title_success if success else title_fail
        color = discord.Color.dark_green() if success else discord.Color.red()
        super().__init__(title, description, color)


class UserActionEmbed(BaseEmbed):
    """A class based on BaseEmbed which sets the author to the user who triggered the action."""

    def __init__(self, itr: discord.Interaction, title: str, description: str):
        super().__init__("", description, color=discord.Color(UserColor.get(itr)))
        self.set_author(name=title, icon_url=itr.user.display_avatar.url)


class NoResultsFoundEmbed(BaseEmbed):
    def __init__(self, name: str, query: str):
        super().__init__(f"No {name} found.", f"No results found for '{query}'.", color=discord.Color.red())


class ErrorEmbed(BaseEmbed):
    def __init__(self, error: str):
        super().__init__("Error!", f"{error}", color=discord.Color.red())
