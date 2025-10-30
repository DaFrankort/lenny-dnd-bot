import discord

from embed import SuccessEmbed
from embeds.color import ColorSetEmbed, ColorShowEmbed
from command import SimpleCommand, SimpleCommandGroup
from logic.color import UserColor, save_hex_color, save_rgb_color


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

    async def callback(self, itr: discord.Interaction, hex_color: str):
        self.log(itr)
        result = save_hex_color(itr, hex_color)
        embed = ColorSetEmbed(itr, result, hex=True)
        await itr.response.send_message(embed=embed, file=embed.file, ephemeral=True)


class ColorSetRGBCommand(SimpleCommand):
    name = "rgb"
    desc = "Set a preferred color using rgb values."
    help = "Set a custom color for yourself by providing a RGB value."

    async def callback(
        self,
        itr: discord.Interaction,
        r: discord.app_commands.Range[int, 0, 255],
        g: discord.app_commands.Range[int, 0, 255],
        b: discord.app_commands.Range[int, 0, 255],
    ):
        self.log(itr)
        result = save_rgb_color(itr, r, g, b)
        embed = ColorSetEmbed(itr, result, hex=False)
        await itr.response.send_message(embed=embed, file=embed.file, ephemeral=True)


class ColorShowCommand(SimpleCommand):
    name = "show"
    desc = "Show off your current color!"
    help = "Shows the color that you are currently using publicly."

    async def callback(self, itr: discord.Interaction):
        self.log(itr)
        color = UserColor.get(itr)
        embed = ColorShowEmbed(itr, color)
        await itr.response.send_message(embed=embed, file=embed.file)


class ColorClearCommand(SimpleCommand):
    name = "clear"
    desc = "Clear your preferred color."
    help = "Set your color back to an auto-generated one."

    async def callback(self, itr: discord.Interaction):
        self.log(itr)
        removed = UserColor.remove(itr)
        embed = SuccessEmbed(
            title_success="Cleared user-defined color.",
            title_fail="You have not yet set a color.",
            description="",
            success=removed,
        )
        await itr.response.send_message(embed=embed, ephemeral=True)
