import io
import discord

from embeds import UserActionEmbed
from logger import log_cmd
from methods import when
from user_colors import UserColor
from PIL import Image, ImageDraw, ImageFont


class ColorCommandGroup(discord.app_commands.Group):
    name = "color"
    desc = "Set a preferred color to easily identify your actions!"

    def __init__(self):
        super().__init__(name=self.name, description=self.desc)
        self.add_command(ColorSetCommandGroup())
        self.add_command(ColorShowCommand())
        self.add_command(ColorClearCommand())


class ColorSetCommandGroup(discord.app_commands.Group):
    name = "set"
    desc = "Set a preferred color."

    def __init__(self):
        super().__init__(name=self.name, description=self.desc)
        self.add_command(ColorSetHexCommand())
        self.add_command(ColorSetRGBCommand())


class ColorSetHexCommand(discord.app_commands.Command):
    name = "hex"
    desc = "Set a preferred color using a hex-value."
    help = "Set a custom color for yourself by providing a hex value."
    command = "/color set hex <color>"

    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.desc,
            callback=self.callback,
        )

    async def callback(self, itr: discord.Interaction, hex_color: str):
        log_cmd(itr)

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


class ColorSetRGBCommand(discord.app_commands.Command):
    name = "rgb"
    desc = "Set a preferred color using rgb values."
    help = "Set a custom color for yourself by providing a rgb values."
    command = "/color set rgb <r> <g> <b>"

    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.desc,
            callback=self.callback,
        )

    async def callback(
        self,
        itr: discord.Interaction,
        r: discord.app_commands.Range[int, 0, 255],
        g: discord.app_commands.Range[int, 0, 255],
        b: discord.app_commands.Range[int, 0, 255],
    ):
        log_cmd(itr)

        ro, go, bo = UserColor.to_rgb(UserColor.get(itr))
        old_rgb_str = f"R ``{ro:03}``, G ``{go:03}``, B ``{bo:03}``"
        new_rgb_str = f"R ``{r:03}``, G ``{g:03}``, B ``{b:03}``"
        color = discord.Color.from_rgb(r, g, b).value
        UserColor.save(itr, color)
        await itr.response.send_message(
            embed=UserActionEmbed(
                itr=itr,
                title=f"{itr.user.display_name} set a new color!",
                description=f"{old_rgb_str} => {new_rgb_str}",
            ),
            ephemeral=True,
        )


class ColorShowCommand(discord.app_commands.Command):
    name = "show"
    desc = "Show your current color."
    help = "Shows the color that you are currently using"
    command = "/color show"

    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.desc,
            callback=self.callback,
        )

    async def callback(self, itr: discord.Interaction):
        log_cmd(itr)

        color = UserColor.get(itr)
        hex = f"#{color:06X}"
        r, g, b = UserColor.to_rgb(color)

        # GEN PALETTE IMAGE
        image = Image.new("RGBA", (256, 256), (r, g, b, 255))
        draw = ImageDraw.Draw(image)

        font_size = 16
        luminance = 0.2126*r + 0.7152*g + 0.0722*b  # Use luminance to decide font color
        font_color = "black" if luminance > 128 else "white"
        try:
            font = ImageFont.truetype(
                font="./assets/fonts/GoogleSansCode-Light.ttf", size=font_size
            )
        except OSError:
            font = ImageFont.load_default(size=font_size)

        image_text = hex
        padding = font_size // 2
        y = padding
        line_height = int((font.getbbox("A")[3] - font.getbbox("A")[1]) * 1.5)
        for line in image_text.split("\n"):
            draw.text((padding, y), line, font=font, fill=font_color)
            y += line_height

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        file = discord.File(fp=buffer, filename="color.png")

        embed = UserActionEmbed(itr=itr, title="Your current color", description=hex)
        embed.set_image(url=f"attachment://{file.filename}")
        await itr.response.send_message(embed=embed, file=file)


class ColorClearCommand(discord.app_commands.Command):
    name = "clear"
    desc = "Clear your preferred color."
    help = "Set your color back to an auto-generated one."
    command = "/color clear"

    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.desc,
            callback=self.callback,
        )

    async def callback(self, itr: discord.Interaction):
        log_cmd(itr)

        removed = UserColor.remove(itr)
        message = when(
            removed,
            "❌ Cleared user-defined color. ❌",
            "⚠️ You have not yet set a color. ⚠️",
        )
        await itr.response.send_message(message, ephemeral=True)
