import discord
from logic.color import UserColor


class SimpleEmbed(discord.Embed):
    def __init__(self, title: str, description: str | None, color: discord.Color = None) -> None:
        if not color:
            color = discord.Color.dark_green()

        super().__init__(
            color=color,
            title=title,
            type="rich",
            url=None,
            description=None,
            timestamp=None,
        ),

        if description:
            self.add_field(name="", value=description)


class SuccessEmbed(SimpleEmbed):
    """A class based on SimpleEmbed which easily toggles the color from green to red."""

    def __init__(
        self,
        title_success: str,
        title_fail: str,
        description: str | None,
        success: bool,
    ):
        title = title_success if success else title_fail
        color = discord.Color.dark_green() if success else discord.Color.red()
        super().__init__(title, description, color)


class UserActionEmbed(SimpleEmbed):
    """A class based on SimpleEmbed which sets the author to the user who triggered the action."""

    def __init__(self, itr: discord.Interaction, title: str, description: str):
        super().__init__(
            "",
            description,
            color=UserColor.get(itr),
        ),
        self.set_author(
            name=title,
            icon_url=itr.user.display_avatar.url,
        )


class NoResultsFoundEmbed(SimpleEmbed):
    def __init__(self, name: str, query: str):
        super().__init__(
            f"No {name} found.",
            f"No results found for '{query}'.",
            color=discord.Color.red(),
        )


class ErrorEmbed(SimpleEmbed):
    def __init__(self, error: str):
        super().__init__(
            "Error!",
            f"{error}",
            color=discord.Color.red(),
        )
