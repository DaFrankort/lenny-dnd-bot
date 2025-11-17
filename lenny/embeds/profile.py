import discord
from discord import Interaction

from embeds.embed import SimpleEmbed
from logic.color import UserColor
from logic.profile import ProfileEntry


class ProfileEmbed(SimpleEmbed):
    def __init__(self, itr: Interaction, profile: ProfileEntry):
        color = discord.Color(UserColor.get(itr))
        super().__init__(title=profile.name, description="", color=color)
        self.set_thumbnail(url=profile.img_url or itr.user.display_avatar.url)
        self.set_author(name=f"{itr.user.name.title()}'s profile", icon_url=None)
