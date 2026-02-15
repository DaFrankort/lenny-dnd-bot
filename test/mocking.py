import time
from enum import Enum
from unittest.mock import AsyncMock, MagicMock

import discord

from bot import Bot


class ExternalAsset(str, Enum):
    GIF = "https://media1.tenor.com/m/eTAoIPj7DdIAAAAC/pokemon-pikachu.gif"
    IMAGE = "https://archives.bulbagarden.net/media/upload/4/4a/0025Pikachu.png"
    IMAGE_FACE = "https://archives.bulbagarden.net/media/upload/c/cd/Ash_JN.png"
    AVATAR = "https://archives.bulbagarden.net/media/upload/c/c1/0025Pikachu-PhD.png"
    SOUND = "https://raw.githubusercontent.com/PokeAPI/cries/main/cries/pokemon/latest/25.ogg"
    BACKGROUND = "https://archives.bulbagarden.net/media/upload/d/dd/Professor_Oak_Laboratory_M20.png"


class MockBot(Bot):
    def __init__(self):
        super().__init__(voice=False)
        self.register_commands()


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
            # Required for mocking, as adding members normally requires a HTTP request
            member._roles.add(role.id)  # type: ignore
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

    @property
    def avatar(self):
        return MockImageAsset()


class MockMember(discord.Member):
    def __init__(self, user: MockUser, guild: discord.Guild, admin: bool):
        self._roles = discord.utils.SnowflakeList(map(int, {}))
        self.timed_out_until = None
        self._user = user
        self.guild = guild
        self.guild_permissions.administrator = admin


class MockTextChannel(discord.TextChannel):
    def __init__(self, guild: discord.Guild = MockGuild(999), id: int = 100):
        self.guild = guild
        self.id = id


class MockInteraction(discord.Interaction):
    """Mock interaction class to simulate Discord interactions."""

    def __init__(self, user: MockUser = MockUser("user"), guild_id: int = 999, channel_id: int = 100):
        mock_guild = MockGuild(guild_id)
        self.user = user
        self.guild_id = guild_id
        self.channel = MockTextChannel(mock_guild, channel_id)

        self.response = MagicMock()
        self.response.send_message = AsyncMock()
        self.response.defer = AsyncMock()
        self.followup = AsyncMock()
        self._client = MagicMock()
        self._client.user = self.user
        self._state = MagicMock()
        self._servers = MagicMock()
        self._original_response = MagicMock()
        self._state._get_guild = MagicMock(return_value=mock_guild)


class MockDMChannel(discord.DMChannel):
    def __init__(self, user: discord.User):
        self.recipients = [user]
        self.id = 0


class MockDirectMessageInteraction(discord.Interaction):
    """Mock interaction class to simulate Discord interactions in direct messages."""

    def __init__(self, user: MockUser = MockUser("user")):
        self.user = user
        self.guild_id = None
        self.channel = MockDMChannel(user)

        self.response = MagicMock()
        self.response.send_message = AsyncMock()
        self.response.defer = AsyncMock()
        self.followup = AsyncMock()
        self._state = MagicMock()
        self._servers = MagicMock()
        self._original_response = MagicMock()
        self._state._get_guild = MagicMock(return_value=None)


class MockAttachment(discord.Attachment):
    def __init__(self, url: str, content_type: str, id: int | None = None):
        self.id = abs(hash(url)) if id is None else id
        self.url = url
        self.filename = f"file.{self.id}.data"
        self.content_type = content_type
        self.read = AsyncMock()
        self.read.return_value = bytes()


class MockImage(MockAttachment):
    def __init__(self, has_face: bool = True, id: int | None = None):
        if has_face:
            url = ExternalAsset.IMAGE_FACE.value
        else:
            url = ExternalAsset.IMAGE.value
        super().__init__(url, "image", id)


class MockGIFImage(MockAttachment):
    def __init__(self):
        url = ExternalAsset.GIF.value
        super().__init__(url, "image")


class MockBackgroundImage(MockAttachment):
    def __init__(self):
        url = ExternalAsset.BACKGROUND.value
        super().__init__(url, "image")


class MockSound(MockAttachment):
    def __init__(self):
        url = ExternalAsset.SOUND.value
        super().__init__(url, "audio")


class MockImageAsset(discord.Asset):
    def __init__(self):
        self._state = MagicMock()
        self._url = ExternalAsset.AVATAR.value
        self._key = str(hash(self.url))
        self._animated = False


class MockMessage(discord.Message):
    def __init__(self, user: discord.User, channel: discord.TextChannel = MockTextChannel(), content: str = "") -> None:
        # The id is the amount of nanoseconds since epoch
        self.id = round(time.time() * 1e9)
        self.author = user
        self.channel = channel
        self.content = content
        self._state = MagicMock()

    async def delete(self, *, delay: float | None = None) -> None:
        # Overwritten because we don't want to actually delete discord messages.
        # This is purely to mock behavior.
        return


class MockEmbed(discord.Embed):
    def __init__(self, title: str, author: str = "", contents: str = ""):
        super().__init__(title=title)
        self.set_author(name=author)
        self.add_field(name="", value=contents)
