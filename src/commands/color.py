import discord

from app_commands import SimpleCommand, SimpleCommandGroup
from embeds import UserActionEmbed
from methods import when
from user_colors import UserColor


class ColorCommandGroup(SimpleCommandGroup):
    name = "color"
    desc = "Set a preferred color to easily identify your actions!"

    def __init__(self):
        super().__init__()
        self.add_command(ColorSetCommand())
        self.add_command(ColorClearCommand())


class ColorSetCommand(SimpleCommand):
    name = "set"
    desc = "Set a preferred color using a hex-value."
    help = "Set a custom color for yourself by providing a hex value."

    def __init__(self):
        super().__init__()

    async def callback(self, itr: discord.Interaction, hex_color: str):
        self.log(itr)

        if not UserColor.validate(hex_color):
            await itr.response.send_message(
                "⚠️ Invalid hex value: Must be 6 valid hexadecimal characters (0-9, A-F), optionally starting with a # symbol. (eg. ff00ff / #ff00ff) ⚠️",
                ephemeral=True,
            )
            return

        old_color = f"#{UserColor.get(itr):06X}"
        color = UserColor.parse(hex_color)
        UserColor.save(itr, color)
        await itr.response.send_message(
            embed=UserActionEmbed(
                itr=itr,
                title=f"{itr.user.display_name} set a new color!",
                description=f"``{old_color.upper()}`` => ``#{hex_color.upper()}``",
            ),
            ephemeral=True,
        )


class ColorClearCommand(SimpleCommand):
    name = "clear"
    desc = "Clear your preferred color."
    help = "Set your color back to an auto-generated one."

    def __init__(self):
        super().__init__()

    async def callback(self, itr: discord.Interaction):
        self.log(itr)

        removed = UserColor.remove(itr)
        message = when(
            removed,
            "❌ Cleared user-defined color. ❌",
            "⚠️ You have not yet set a color. ⚠️",
        )
        await itr.response.send_message(message, ephemeral=True)
