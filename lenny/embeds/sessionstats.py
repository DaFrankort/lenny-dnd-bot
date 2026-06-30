from embeds.embed import BaseEmbed
from logic.session.stats import UserSessionResult


class UserSessionStatEmbed(BaseEmbed):
    def __init__(self, user_result: UserSessionResult):
        super().__init__(title=user_result.title, description=user_result.description, color=user_result.color)

        self.set_author(name=user_result.user.display_name, icon_url=user_result.user.display_avatar.url)
