import discord
from discord.app_commands import Choice, autocomplete, choices, describe

from commands.command import BaseCommand, BaseCommandGroup
from embeds.color import ColorSetEmbed, ColorShowEmbed
from embeds.embed import SuccessEmbed
from logic.color import (
    BasicColors,
    ImageColorStyle,
    UserColor,
    save_base_color,
    save_hex_color,
    save_image_color,
    save_rgb_color,
)


async def autocomplete_hex_color(itr: discord.Interaction, current: str) -> list[Choice[str]]:
    """
    Suggests the current hex-color the user is using if no input has been done yet.
    If there is an input, will auto-format the input to be the correct length.
    """
    current_clean: str = current.replace("#", "").replace(" ", "").strip()
    if not current_clean:  # Show current color if no input
        color = UserColor.get(itr)
        hex_color = UserColor.to_hex(color)
        return [Choice(name=hex_color, value=hex_color)]

    # Enforce 6-characters
    current_clean = (current_clean[:6]).ljust(6, "0")
    hex_color = f"#{current_clean}"
    return [Choice(name=hex_color, value=hex_color)]


async def autocomplete_rgb_color(itr: discord.Interaction, current: str) -> list[Choice[str]]:
    """Suggests the current value the user has for each argument (R/G/B), if no input has been done yet."""
    current = str(current)
    if current:
        return []

    itr_options: list[dict] | None = itr.data["options"][0]["options"][0]["options"]  # type: ignore
    if not itr_options:
        return []

    focused: str = [arg["name"] for arg in itr_options if arg.get("focused", False)][0]  # type: ignore
    if not focused:
        return []

    r, g, b = UserColor.to_rgb(UserColor.get(itr))
    color_map = {"r": r, "g": g, "b": b}
    value = color_map.get(focused, None)  # pyright: ignore[reportUnknownArgumentType]
    if value is None:
        return []
    return [Choice(name=str(value), value=str(value))]


class ColorCommandGroup(BaseCommandGroup):
    name = "color"
    desc = "Set a preferred color to easily identify your actions!"

    def __init__(self):
        super().__init__()
        self.add_command(ColorSetCommandGroup())
        self.add_command(ColorShowCommand())
        self.add_command(ColorClearCommand())


class ColorSetCommandGroup(BaseCommandGroup):
    name = "set"
    desc = "Set a preferred color."

    def __init__(self):
        super().__init__()
        self.add_command(ColorSetHexCommand())
        self.add_command(ColorSetRGBCommand())
        self.add_command(ColorSetBaseCommand())
        self.add_command(ColorSetImageCommand())


class ColorSetHexCommand(BaseCommand):
    name = "hex"
    desc = "Set a preferred color using a hex-value."
    help = "Set a custom color for yourself by providing a hex value."

    @describe(hex_color="A hexadecimal value representing a color (Example: #ff00ff or aa44cc).")
    @autocomplete(hex_color=autocomplete_hex_color)
    async def handle(self, itr: discord.Interaction, hex_color: str):
        result = save_hex_color(itr, hex_color)
        embed = ColorSetEmbed(itr, result, is_hex=True)
        await itr.response.send_message(embed=embed, file=embed.file, ephemeral=True)


class ColorSetRGBCommand(BaseCommand):
    name = "rgb"
    desc = "Set a preferred color using rgb values."
    help = "Set a custom color for yourself by providing a RGB value."

    @describe(
        r="A value from 0-255 representing the amount of red.",
        g="A value from 0-255 representing the amount of green.",
        b="A value from 0-255 representing the amount of blue.",
    )
    @autocomplete(
        r=autocomplete_rgb_color,
        g=autocomplete_rgb_color,
        b=autocomplete_rgb_color,
    )
    async def handle(
        self,
        itr: discord.Interaction,
        r: discord.app_commands.Range[int, 0, 255],
        g: discord.app_commands.Range[int, 0, 255],
        b: discord.app_commands.Range[int, 0, 255],
    ):
        result = save_rgb_color(itr, r, g, b)
        embed = ColorSetEmbed(itr, result, is_hex=False)
        await itr.response.send_message(embed=embed, file=embed.file, ephemeral=True)


class ColorSetBaseCommand(BaseCommand):
    name = "base"
    desc = "Select a preferred color from a list of basic colors."
    help = "Set a custom color for yourself by selecting a basic color."

    @describe(color="The color you'd like to use for display.")
    @choices(color=BasicColors.choices())
    async def handle(
        self,
        itr: discord.Interaction,
        color: int,
    ):
        result = save_base_color(itr, color)
        embed = ColorSetEmbed(itr, result, is_hex=True)
        await itr.response.send_message(embed=embed, file=embed.file, ephemeral=True)


class ColorSetImageCommand(BaseCommand):
    name = "image"
    desc = "Choose a color from a palette generated from an image."
    help = "Pick a color from a palette generated from an image. If no image is provided, your server avatar will be used."

    @describe(
        image="Alternative image to base your colors on, uses your server-avatar if left empty.",
        style="(Default = Realistic); Adjusts the color-style of the generated colors.",
    )
    @choices(style=ImageColorStyle.choices())
    async def handle(
        self,
        itr: discord.Interaction,
        image: discord.Attachment | None = None,
        style: int = ImageColorStyle.REALISTIC.value,
    ):
        result = await save_image_color(itr, image, ImageColorStyle(style))
        embed = ColorSetEmbed(itr, result, is_hex=True)
        if embed.view:
            await itr.response.send_message(embed=embed, view=embed.view, file=embed.file, ephemeral=True)
            return
        await itr.response.send_message(embed=embed, file=embed.file, ephemeral=True)


class ColorShowCommand(BaseCommand):
    name = "show"
    desc = "Show off your current color!"
    help = "Shows the color that you are currently using publicly."

    async def handle(self, itr: discord.Interaction):
        color = UserColor.get(itr)
        embed = ColorShowEmbed(itr, color)
        await itr.response.send_message(embed=embed, file=embed.file)


class ColorClearCommand(BaseCommand):
    name = "clear"
    desc = "Clear your preferred color."
    help = "Set your color back to an auto-generated one."

    async def handle(self, itr: discord.Interaction):
        removed = UserColor.remove(itr)
        embed = SuccessEmbed(
            title_success="Cleared user-defined color.",
            title_fail="You have not yet set a color.",
            description="",
            success=removed,
        )
        await itr.response.send_message(embed=embed, ephemeral=True)
