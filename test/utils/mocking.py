from unittest.mock import MagicMock

import discord


class MockRole(discord.Role):
    def __init__(self, name: str, guild: discord.Guild):
        self.id = abs(hash(name))
        self.name = name
        self.guild = guild
        self.position = len(name)


class MockGuild(discord.Guild):
    def __init__(self, id: int):
        self.id = id
        self._roles = {}
        self._members = {}

        owner = MockUser("admin")
        self.owner_id = owner.id

        # Add roles and users
        player_role = MockRole("player", self)
        onlooker_role = MockRole("onlooker", self)
        gamemaster_role = MockRole("game master", self)

        self._add_role(player_role)
        self._add_role(onlooker_role)
        self._add_role(gamemaster_role)

        player_count = 5
        onlooker_count = 10
        gamemaster_count = 2

        for player in range(player_count):
            self.create_member(f"player {player}", [player_role], False)

        for onlooker in range(onlooker_count):
            self.create_member(f"onlooker {onlooker}", [onlooker_role], False)

        for gamemaster in range(gamemaster_count):
            self.create_member(f"game master {gamemaster}", [gamemaster_role], False)

    def create_member(self, name: str, roles: list[discord.Role], admin: bool) -> discord.Member:
        member = MockMember(MockUser(name), self, admin)
        self._add_member(member)
        for role in roles:
            member._roles.add(role.id)
        return member


class MockUser(discord.User):
    """Mock user class to simulate Discord users."""

    def __init__(self, name: str):
        self.id = abs(hash(name))
        self.name = name
        self.global_name = name
        self.discriminator = str(self.id)
        self._avatar = MagicMock()
        self._state = MagicMock()


class MockMember(discord.Member):
    def __init__(self, user: MockUser, guild: discord.Guild, admin: bool):
        self._roles = discord.utils.SnowflakeList(map(int, {}))
        self.timed_out_until = None
        self._user = user
        self.guild = guild
        self.guild_permissions.administrator = admin


class MockInteraction(discord.Interaction):
    """Mock interaction class to simulate Discord interactions."""

    def __init__(self, user: MockUser = MockUser("user"), guild_id: int = 999):
        self.user = user
        self.guild_id = guild_id


def _mock_attachment(url: str, content_type: str) -> discord.Attachment:
    attachment = MagicMock(spec=discord.Attachment)
    attachment.url = url
    attachment.content_type = MagicMock()
    attachment.content_type = content_type
    return attachment


def mock_image() -> discord.Attachment:
    img_url = r"https://img.lovepik.com/element/40116/9419.png_1200.png"
    return _mock_attachment(img_url, "image")


def mock_sound() -> discord.Attachment:
    sound_url = r"https://diviextended.com/wp-content/uploads/2021/10/sound-of-waves-marine-drive-mumbai.mp3"
    return _mock_attachment(sound_url, "audio")
