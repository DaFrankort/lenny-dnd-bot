import io
import discord

from logic.app_commands import SimpleCommand, SimpleCommandGroup
from embeds2 import UserActionEmbed
from methods import FontType, get_font, when
from user_colors import UserColor
from PIL import Image, ImageDraw


def get_palette_image(color: discord.Color | int) -> discord.File:
    if isinstance(color, discord.Color):
        color = color.value
    r, g, b = UserColor.to_rgb(color)
    hex_str = f"#{color:06X}"

    # Draw square
    image = Image.new("RGBA", (256, 64), (r, g, b, 255))
    draw = ImageDraw.Draw(image)

    # Draw text
    font_size = 16
    luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
    font_color = when(luminance > 0.5, "black", "white")
    font = get_font(FontType.MONOSPACE, font_size)

    bbox = draw.textbbox((0, 0), hex_str, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    x = (image.width - text_w) // 2
    y = (image.height - text_h) // 2 - (font_size // 4)

    draw.text((x, y), hex_str, font=font, fill=font_color)

    # Buffer and send
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return discord.File(fp=buffer, filename="color.png")


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

        if not UserColor.validate(hex_color):
            await itr.response.send_message(
                "⚠️ Invalid hex value: Must be 6 valid hexadecimal characters (0-9, A-F), optionally starting with a # symbol. (eg. ff00ff / #ff00ff) ⚠️",
                ephemeral=True,
            )
            return

        old_color = f"#{UserColor.get(itr):06X}"
        color = UserColor.parse(hex_color)
        UserColor.save(itr, color)
        file = get_palette_image(color)

        embed = UserActionEmbed(
            itr=itr,
            title=f"{itr.user.display_name} set a new color!",
            description=f"``{old_color.upper()}`` => ``#{hex_color.upper()}``",
        )
        embed.set_image(url=f"attachment://{file.filename}")
        await itr.response.send_message(embed=embed, file=file, ephemeral=True)


class ColorSetRGBCommand(SimpleCommand):
    name = "rgb"
    desc = "Set a preferred color using rgb values."
    help = "Set a custom color for yourself by providing a rgb values."

    async def callback(
        self,
        itr: discord.Interaction,
        r: discord.app_commands.Range[int, 0, 255],
        g: discord.app_commands.Range[int, 0, 255],
        b: discord.app_commands.Range[int, 0, 255],
    ):
        self.log(itr)

        ro, go, bo = UserColor.to_rgb(UserColor.get(itr))
        description = f"R ``{ro:03}`` => ``{r:03}``\nG ``{go:03}`` => ``{g:03}``\nB ``{bo:03}`` => ``{b:03}``"
        color = discord.Color.from_rgb(r, g, b).value
        UserColor.save(itr, color)
        file = get_palette_image(color)

        embed = UserActionEmbed(
            itr=itr,
            title=f"{itr.user.display_name} set a new color!",
            description=description,
        )
        embed.set_image(url=f"attachment://{file.filename}")
        await itr.response.send_message(embed=embed, file=file, ephemeral=True)


class ColorShowCommand(SimpleCommand):
    name = "show"
    desc = "Show off your current color!"
    help = "Shows the color that you are currently using publically."

    async def callback(self, itr: discord.Interaction):
        self.log(itr)

        color = UserColor.get(itr)
        title = f"{itr.user.display_name}'s color!"
        file = get_palette_image(color)

        embed = UserActionEmbed(itr=itr, title=title, description="")
        embed.set_image(url=f"attachment://{file.filename}")
        await itr.response.send_message(embed=embed, file=file)


class ColorClearCommand(SimpleCommand):
    name = "clear"
    desc = "Clear your preferred color."
    help = "Set your color back to an auto-generated one."

    async def callback(self, itr: discord.Interaction):
        self.log(itr)

        removed = UserColor.remove(itr)
        message = when(
            removed,
            "❌ Cleared user-defined color. ❌",
            "⚠️ You have not yet set a color. ⚠️",
        )
        await itr.response.send_message(message, ephemeral=True)
