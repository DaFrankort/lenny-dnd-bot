from profile import Profile
from discord import Color, Interaction, ui
from components.items import SimpleSeparator
from embed import SimpleEmbed
from logic.color import UserColor
from logic.profile import ProfileList


class ProfileEmbed(SimpleEmbed):
    def __init__(self, itr: Interaction, profile: Profile):
        super().__init__(title=profile.name, description="", color=UserColor.get(itr))
        self.set_thumbnail(url=profile.image_url or itr.user.display_avatar.url)
        self.set_author(name=f"{itr.user.name.title()}'s profile", icon_url=None)
