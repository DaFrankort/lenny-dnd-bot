import discord


class MockUser:
    """Mock user class to simulate Discord users."""

    def __init__(self, user_id: int = 123, display_name: str = "Foo"):
        self.id = user_id
        self.display_name = display_name


class MockInteraction(discord.Interaction):
    """Mock interaction class to simulate Discord interactions."""

    def __init__(self, user: MockUser = MockUser(), guild_id: int = 999):
        self.user = user
        self.guild_id = guild_id
