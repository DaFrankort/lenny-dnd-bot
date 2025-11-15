import discord


class ConfigAllowButton(discord.ui.Button[discord.ui.LayoutView]):
    """Helper class to show an enable/disable button in config overviews."""

    allowed: bool  # Is the current button'state set to enabled or disabled?

    def __init__(self, allowed: bool, disabled: bool):
        super().__init__()

        self.allowed = allowed
        self.disabled = disabled
        if self.allowed:
            self.label = "‎ Enabled ‎‎"
            self.style = discord.ButtonStyle.green
        else:
            self.label = "Disabled"
            self.style = discord.ButtonStyle.red
