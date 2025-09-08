from unittest.mock import MagicMock

import discord

IMG_URL = r"https://img.lovepik.com/element/40116/9419.png_1200.png"


class MockUser:
    """Mock user class to simulate Discord users."""

    def __init__(self, user_id: int = 123, display_name: str = "Foo"):
        self.id = user_id
        self.display_name = display_name


class MockInteraction:
    """Mock interaction class to simulate Discord interactions."""

    def __init__(self, user: MockUser = MockUser(), guild_id: int = 999):
        self.user = user
        self.guild_id = guild_id


def _mock_attachment(url: str, content_type: str) -> discord.Attachment:
    attachment = MagicMock(spec=discord.Attachment)
    attachment.url = url
    attachment.content_type = MagicMock()
    attachment.content_type = content_type
    return attachment


def mock_image() -> discord.Attachment:
    return _mock_attachment(IMG_URL, "image")


def mock_sound() -> discord.Attachment:
    sound_url = r"https://diviextended.com/wp-content/uploads/2021/10/sound-of-waves-marine-drive-mumbai.mp3"
    return _mock_attachment(sound_url, "audio")
