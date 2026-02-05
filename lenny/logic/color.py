import dataclasses
import io
import re
from typing import Literal

import colornames  # type: ignore
import discord
import skimage
from PIL import Image, ImageDraw

from logic.jsonhandler import JsonHandler
from logic.tokengen import open_image_from_attachment, open_image_from_url
from methods import ChoicedEnum, FontType, get_font


class BasicColors(ChoicedEnum):
    RED = discord.Color.red().value
    DARK_RED = discord.Color.dark_red().value
    BRAND_RED = discord.Color.brand_red().value
    ORANGE = discord.Color.orange().value
    DARK_ORANGE = discord.Color.dark_orange().value
    GOLD = discord.Color.gold().value
    DARK_GOLD = discord.Color.dark_gold().value
    YELLOW = discord.Color.yellow().value
    GREEN = discord.Color.green().value
    DARK_GREEN = discord.Color.dark_green().value
    BRAND_GREEN = discord.Color.brand_green().value
    TEAL = discord.Color.teal().value
    DARK_TEAL = discord.Color.dark_teal().value
    BLUE = discord.Color.blue().value
    DARK_BLUE = discord.Color.dark_blue().value
    BLURPLE = discord.Color.blurple().value
    OG_BLURPLE = discord.Color.og_blurple().value
    PURPLE = discord.Color.purple().value
    DARK_PURPLE = discord.Color.dark_purple().value
    MAGENTA = discord.Color.magenta().value
    DARK_MAGENTA = discord.Color.dark_magenta().value
    PINK = discord.Color.pink().value
    FUCHSIA = discord.Color.fuchsia().value
    GREYPLE = discord.Color.greyple().value


def _get_luminance_font_color(r: int, g: int, b: int) -> Literal["black", "white"]:
    """Returns black or white based on the background color in RGB, used to make text readable over a background."""
    luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
    if luminance > 0.5:
        return "black"
    return "white"


def get_palette_image(color: discord.Color | int) -> discord.File:
    if isinstance(color, discord.Color):
        color = color.value
    r, g, b = UserColor.to_rgb(color)

    # Draw square
    image = Image.new("RGBA", (256, 64), (r, g, b, 255))
    draw = ImageDraw.Draw(image)

    # Draw text
    font = get_font(FontType.MONOSPACE, size=16)
    lines = [UserColor.to_name(color), UserColor.to_hex(color)]
    spacing = 6
    line_heights = [font.getbbox(line)[3] - font.getbbox(line)[1] for line in lines]
    total_height = sum(line_heights) + spacing * (len(lines) - 1)

    y = (image.height - total_height) // 2 - 4
    for i, line in enumerate(lines):
        line_bbox = draw.textbbox((0, 0), line, font=font)
        line_w = line_bbox[2] - line_bbox[0]
        # Center horizontally
        x = (image.width - line_w) // 2
        draw.text((x, y), line, font=font, fill=_get_luminance_font_color(r, g, b))
        y += line_heights[i] + spacing

    # Buffer and send
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return discord.File(fp=buffer, filename="color.png")


@dataclasses.dataclass
class UserColorSaveResult:
    old_color: int
    color: list[int]


def save_hex_color(itr: discord.Interaction, hex_color: str) -> UserColorSaveResult:
    if not UserColor.validate(hex_color):
        raise SyntaxError(
            "Invalid hex value: Must be 6 valid hexadecimal characters (0-9, A-F), optionally starting with a # symbol. (eg. ff00ff / #ff00ff)"
        )

    old_color = UserColor.get(itr)
    color = UserColor.parse(hex_color)
    UserColor.add(itr, color)

    return UserColorSaveResult(old_color, [color])


def save_rgb_color(itr: discord.Interaction, r: int, g: int, b: int) -> UserColorSaveResult:
    old_color = UserColor.get(itr)
    color = discord.Color.from_rgb(r, g, b).value
    UserColor.add(itr, color)

    return UserColorSaveResult(old_color, [color])


def save_base_color(itr: discord.Interaction, color: int):
    old_color = UserColor.get(itr)
    UserColor.add(itr, color)

    return UserColorSaveResult(old_color, [color])


def _get_delta_e(rgb1: tuple[int, int, int], rgb2: tuple[int, int, int]) -> float:
    """
    Calculates ΔE between two rgb values.

    ΔE is a way to measure how different two colors are in human perception.
    It's represented as a value from 0 to 100 where:
    - <1 = Not perceptible
    - 1-2  = Perceptible through close observation
    - 2-10 = Perceptible at a glance
    - 11-49 = Colors are more similar than opposite.
    - 100 = Colors are exact opposite.

    Source: https://zschuessler.github.io/DeltaE/learn/
    """
    # Convert RGB 0-255 to 0-1 and wrap as 1x1x3 arrays for skimage
    lab1 = skimage.color.rgb2lab([[[rgb1[0] / 255, rgb1[1] / 255, rgb1[2] / 255]]])[0, 0]  # type: ignore
    lab2 = skimage.color.rgb2lab([[[rgb2[0] / 255, rgb2[1] / 255, rgb2[2] / 255]]])[0, 0]  # type: ignore
    return skimage.color.deltaE_ciede2000(lab1, lab2)  # type: ignore


def _get_rgb_chroma(rgb: tuple[float, float, float]) -> float:
    """
    Compute the chroma (vibrancy) of an RGB color.
    """
    lab = skimage.color.rgb2lab([[[rgb[0] / 255, rgb[1] / 255, rgb[2] / 255]]])[0, 0]  # type: ignore
    a, b = lab[1], lab[2]  # type: ignore
    return (a * a + b * b) ** 0.5  # type: ignore


async def save_image_color(
    itr: discord.Interaction, attachment: discord.Attachment | None, complexity: int = 32
) -> UserColorSaveResult:
    avatar = itr.user.display_avatar or itr.user.avatar
    if not avatar:
        raise RuntimeError("You don't have a profile picture set!")

    if not attachment:
        image = await open_image_from_url(avatar.url)
    else:
        image = await open_image_from_attachment(attachment)
    image = image.convert("RGB")

    quantized = image.quantize(colors=complexity, method=2)
    color_counts = quantized.getcolors()
    palette = quantized.getpalette()

    if not color_counts or not palette:
        raise ValueError("Could not retrieve colors from that image!")

    # Group colors from palette by how common they are in the image.
    palette_rgb_colors: list[tuple[int, int, int]] = []  # RGB
    for _, index in color_counts:
        i: int = index * 3  # type: ignore
        palette_rgb_colors.append(((palette[i], palette[i + 1], palette[i + 2])))

    # Filter colors by uniqueness (Using delta-E)
    rgb_colors: list[tuple[int, int, int]] = []  # RGB
    for rgb in palette_rgb_colors:
        if any(_get_delta_e(rgb, rgb2) <= 8 for rgb2 in rgb_colors):
            continue
        # Filter out non-vibrant colors, like black, gray or white.
        if _get_rgb_chroma(rgb) < 8:  # 8 yielded best results whilst testing.
            continue
        rgb_colors.append(rgb)

    if not rgb_colors:
        raise RuntimeError("Could not determine dominant colors.")

    rgb_colors = rgb_colors[:10]
    best_colors = [discord.Color.from_rgb(r, g, b).value for r, g, b in rgb_colors]

    old_color = UserColor.get(itr)
    UserColor.add(itr, best_colors[0])
    return UserColorSaveResult(old_color=old_color, color=best_colors)


class UserColorFileHandler(JsonHandler[int]):
    """Class to handle user colors, which are used in embeds."""

    def __init__(self):
        super().__init__(filename="user_colors")

    def add(self, itr: discord.Interaction, color: int) -> None:
        """Saves the user's color to a JSON file."""
        self.data[str(itr.user.id)] = color
        self.save()

    def validate(self, hex_color: str) -> bool:
        """Validates if the given hex color is in the correct format."""
        hex_color = hex_color.strip("#")
        pattern = re.compile(r"^[0-9a-fA-F]{6}$")
        return pattern.match(hex_color) is not None

    def parse(self, hex_color: str) -> int:
        """Parses a hex color string and returns its integer value."""
        if not hex_color.startswith("#"):
            hex_color = f"#{hex_color}"
        return discord.Color.from_str(hex_color).value

    def generate(self, seed: discord.Interaction | str) -> int:
        """
        Generates a hex value from a username.
        Converts the first 6 characters of a user's display name into a hex value for color.
        """
        hex_value = ""
        hex_place = 0

        if isinstance(seed, discord.Interaction):
            seed = seed.user.display_name

        # This cute little function converts characters into unicode
        # I made it so the the alpha_value assignment line wouldn't be so hard to read
        def get_alpha(char: str):
            return abs(ord(char.lower()) - 96)

        for hex_place in range(0, 6, 2):
            try:
                alpha_curr = get_alpha(seed[hex_place])
                alpha_next = get_alpha(seed[hex_place + 1])
                alpha_value = alpha_curr * alpha_next
            except IndexError:
                # When username is shorter than 6 characters, inserts replacement value.
                # Value can be changed to 255 for light and blue colors, 0 for dark and red colors.
                alpha_value = 0

            if alpha_value > 255:
                alpha_value = alpha_value & 255

            if alpha_value < 16:
                hex_value = hex_value + "0" + hex(alpha_value)[2:]
            else:
                hex_value = hex_value + hex(alpha_value)[2:]

        return UserColor.parse(hex_value)

    def get(self, itr: discord.Interaction) -> int:
        """Retrieves a user's saved color or generates one if it does not exist."""
        color = self.data.get(str(itr.user.id), None)
        if color:
            return color
        return UserColor.generate(itr)

    def remove(self, itr: discord.Interaction) -> bool:
        """Removes a user's saved color from the file."""
        user_id = str(itr.user.id)
        if user_id in self.data:
            self.data.pop(str(itr.user.id))
            self.save()
            return True
        return False

    def to_rgb(self, color: int) -> tuple[int, int, int]:
        return discord.Color(color).to_rgb()

    def to_hex(self, color: int) -> str:
        return f"#{color:06X}".upper()

    def to_name(self, color: int) -> str:
        hex_val = self.to_hex(color)
        # pylint: disable=no-value-for-parameter
        name = colornames.find(hex_val)  # type: ignore
        if isinstance(name, str):
            return name
        return hex_val


UserColor = UserColorFileHandler()
