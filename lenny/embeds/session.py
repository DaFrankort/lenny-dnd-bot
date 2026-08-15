import discord

from embeds.embed import BaseEmbed
from logic.session.stats import UserSessionResult


class UserSessionStatEmbed(BaseEmbed):
    d20_graph: discord.File

    def __init__(self, result: UserSessionResult):
        super().__init__(title=result.title, description=result.description, color=result.color)

        self.set_author(name=result.user.display_name, icon_url=result.user.display_avatar.url)
        if result.graph:
            self.set_image(url=f"attachment://{result.graph.filename}")
