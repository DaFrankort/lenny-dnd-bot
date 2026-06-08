from embeds.embed import BaseEmbed
from logic.sessionsstats import UserSessionResult


class UserSessionStatEmbed(BaseEmbed):

    def __init__(self, user_result: UserSessionResult):
        super().__init__(user_result.title, user_result.description, user_result.color)
        self.set_author(name=user_result.user.display_name, icon_url=user_result.user.display_avatar.url)
