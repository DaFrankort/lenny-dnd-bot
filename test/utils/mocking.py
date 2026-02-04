from unittest.mock import AsyncMock, MagicMock

import discord

from bot import Bot


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
    def __init__(self, guild: discord.Guild, id: int):
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


class MockServerTextChannel(discord.TextChannel):
    def __init__(self, guild: discord.Guild = MockGuild(999)):
        self.guild = guild


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
    def __init__(self, url: str, content_type: str):
        self.id = abs(hash(url))
        self.url = url
        self.filename = "file.data"
        self.content_type = content_type


class MockImage(MockAttachment):
    def __init__(self, has_face: bool = True):
        if has_face:
            url = r"https://img.freepik.com/free-photo/young-bearded-man-with-striped-shirt_273609-5677.jpg?semt=ais_hybrid&w=740&q=80"
        else:
            url = r"https://img.lovepik.com/element/40116/9419.png_1200.png"
        super().__init__(url, "image")


class MockGIFImage(MockAttachment):
    def __init__(self):
        url = r"https://static.klipy.com/ii/d7aec6f6f171607374b2065c836f92f4/ec/f3/OXB1QWhn.gif"
        super().__init__(url, "image")


class MockSound(MockAttachment):
    def __init__(self):
        url = r"https://diviextended.com/wp-content/uploads/2021/10/sound-of-waves-marine-drive-mumbai.mp3"
        super().__init__(url, "audio")


class MockImageAsset(discord.Asset):
    def __init__(self):
        self._state = MagicMock()
        self._url = "https://i.etsystatic.com/10819873/r/il/5452b6/3900731377/il_794xN.3900731377_57vj.jpg"
        self._key = str(hash(self.url))
        self._animated = False


class MockServerTextMessage(discord.Message):
    def __init__(self, user: discord.User, channel: discord.TextChannel) -> None:
        self.author = user
        self.channel = channel
        self._state = MagicMock()

    async def delete(self, *, delay: float | None = None) -> None:
        # Overwritten because we don't want to actually delete discord messages.
        # This is purely to mock behavior.
        return


class MockTextMessageEmbed(discord.Embed):
    def __init__(self, title: str):
        super().__init__(title=title)
