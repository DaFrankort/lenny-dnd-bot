import discord
from discord.app_commands import autocomplete, describe

from commands.command import SimpleCommand, SimpleCommandGroup
from embeds.color import ColorSetEmbed, ColorShowEmbed
from embeds.embed import SuccessEmbed
from logic.color import (
    UserColor,
    autocomplete_hex_color,
    save_hex_color,
    save_rgb_color,
)


class ColorCommandGroup(SimpleCommandGroup):
    name = "color"
    desc = "Set a preferred color to easily identify your actions!"

    def __init__(self):
        super().__init__()
        self.add_command(ColorSetCommandGroup())
        self.add_command(ColorShowCommand())
        self.add_command(ColorClearCommand())


class ColorSetCommandGroup(SimpleCommandGroup):
    name = "set"
    desc = "Set a preferred color."

    def __init__(self):
        super().__init__()
        self.add_command(ColorSetHexCommand())
        self.add_command(ColorSetRGBCommand())


class ColorSetHexCommand(SimpleCommand):
    name = "hex"
    desc = "Set a preferred color using a hex-value."
    help = "Set a custom color for yourself by providing a hex value."

    @describe(hex_color="A hexadecimal value representing a color (Example: #ff00ff or aa44cc).")
    @autocomplete(hex_color=autocomplete_hex_color)
    async def handle(self, itr: discord.Interaction, hex_color: str):
        self.log(itr)
        result = save_hex_color(itr, hex_color)
        embed = ColorSetEmbed(itr, result, is_hex=True)
        await itr.response.send_message(embed=embed, file=embed.file, ephemeral=True)


class ColorSetRGBCommand(SimpleCommand):
    name = "rgb"
    desc = "Set a preferred color using rgb values."
    help = "Set a custom color for yourself by providing a RGB value."

    @describe(
        r="A value from 0-255 representing the amount of red.",
        g="A value from 0-255 representing the amount of green.",
        b="A value from 0-255 representing the amount of blue.",
    )
    async def handle(
        self,
        itr: discord.Interaction,
        r: discord.app_commands.Range[int, 0, 255],
        g: discord.app_commands.Range[int, 0, 255],
        b: discord.app_commands.Range[int, 0, 255],
    ):
        self.log(itr)
        result = save_rgb_color(itr, r, g, b)
        embed = ColorSetEmbed(itr, result, is_hex=False)
        await itr.response.send_message(embed=embed, file=embed.file, ephemeral=True)


class ColorShowCommand(SimpleCommand):
    name = "show"
    desc = "Show off your current color!"
    help = "Shows the color that you are currently using publicly."

    async def handle(self, itr: discord.Interaction):
        self.log(itr)
        color = UserColor.get(itr)
        embed = ColorShowEmbed(itr, color)
        await itr.response.send_message(embed=embed, file=embed.file)


class ColorClearCommand(SimpleCommand):
    name = "clear"
    desc = "Clear your preferred color."
    help = "Set your color back to an auto-generated one."

    async def handle(self, itr: discord.Interaction):
        self.log(itr)
        removed = UserColor.remove(itr)
        embed = SuccessEmbed(
            title_success="Cleared user-defined color.",
            title_fail="You have not yet set a color.",
            description="",
            success=removed,
        )
        await itr.response.send_message(embed=embed, ephemeral=True)
