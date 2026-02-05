import dataclasses
import io
import re

import colornames  # type: ignore
import discord
import numpy as np
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


def _adjust_rgb_color_lightness(rgb: tuple[int, int, int], new_lightness: int) -> tuple[int, int, int]:
    lab = skimage.color.rgb2lab([[[rgb[0] / 255, rgb[1] / 255, rgb[2] / 255]]])[0, 0]  # type: ignore
    lab[0] = np.clip(new_lightness, 0, 100)
    rgb_float = skimage.color.lab2rgb([[lab]])[0, 0]  # type: ignore
    rgb_int = np.clip(rgb_float * 255, 0, 255).astype(int)  # type: ignore
    return tuple(rgb_int)  # type: ignore


def _get_luminance_font_color(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    """
    Returns a brighter font color based on the given background rgb values.
    Has a fallback to pure white or black if the lightened color is too similar to the background color.
    """
    r, g, b = rgb
    luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
    if luminance > 0.5:
        adjusted_rgb = _adjust_rgb_color_lightness(rgb, 20)
        fallback = (0, 0, 0)  # Black
    else:
        adjusted_rgb = _adjust_rgb_color_lightness(rgb, 90)
        fallback = (255, 255, 255)  # White

    if _get_perceived_color_delta(rgb, adjusted_rgb) < 30:
        # 30 is based on the delta we get when we run red (255, 0, 0) through this method.
        # The result for red is hard to read and results in a delta of 24.
        return fallback
    return adjusted_rgb


def get_palette_image(color: discord.Color | int) -> discord.File:
    if isinstance(color, discord.Color):
        color = color.value
    r, g, b = UserColor.to_rgb(color)

    # Draw square
    image = Image.new("RGB", (256, 64), (r, g, b, 255))
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
        draw.text((x, y), line, font=font, fill=_get_luminance_font_color((r, g, b)))
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


def _get_perceived_color_delta(rgb1: tuple[int, int, int], rgb2: tuple[int, int, int]) -> float:
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


class ImageColorStyle(ChoicedEnum):
    REALISTIC = Image.Quantize.FASTOCTREE.value
    COLORFUL = Image.Quantize.MAXCOVERAGE.value
    FADED = Image.Quantize.MEDIANCUT.value


def _get_image_colors(image: Image.Image) -> list[tuple[int, int, int]]:
    """Gets the colors from an image, returns a list of RGB values."""
    color_counts = image.getcolors()
    palette = image.getpalette()

    if not color_counts or not palette:
        raise ValueError("Could not retrieve colors from that image!")

    result: list[tuple[int, int, int]] = []
    for _, index in color_counts:
        i: int = index * 3  # type: ignore
        result.append(((palette[i], palette[i + 1], palette[i + 2])))
    return result


def _filter_most_unique_colors(
    colors: list[tuple[int, int, int]], min_delta_e: float, min_rgb_chroma: float
) -> list[tuple[int, int, int]]:
    """
    Filters a list of RGB colors to keep only visually distinct and sufficiently vibrant ones.
    Args:
        colors: List of RGB color tuples (R, G, B).
        min_delta_e: Minimum perceptual distance (Delta E) required for two colors to be considered visually distinct.
        min_rgb_chroma: Minimum chroma threshold; colors below this value (dark or low-saturation) are discarded.

    Returns:
        A list of RGB tuples representing the most perceptually unique colors.
        If all colors were filtered out, the first five prominent colors are returned instead.
    """
    result: list[tuple[int, int, int]] = []
    for rgb in colors:
        if any(_get_perceived_color_delta(rgb, rgb2) <= min_delta_e for rgb2 in result):
            continue
        if _get_rgb_chroma(rgb) < min_rgb_chroma:
            continue
        result.append(rgb)

    if not result:
        return colors[:5]
    return result


async def save_image_color(
    itr: discord.Interaction, attachment: discord.Attachment | None, style: ImageColorStyle
) -> UserColorSaveResult:
    avatar = itr.user.display_avatar or itr.user.avatar
    if attachment:
        image = await open_image_from_attachment(attachment)
    elif avatar:
        image = await open_image_from_url(avatar.url)
    else:
        raise RuntimeError("You don't have a profile picture set!")

    image = image.convert("RGB")
    quantized = image.quantize(colors=32, method=style.value)
    colors = _get_image_colors(quantized)
    filtered = _filter_most_unique_colors(colors, 8, 8)[:10]  # The values 8 & 8 gave the best results during testing.
    best_colors = [discord.Color.from_rgb(r, g, b).value for r, g, b in filtered]

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
