import dataclasses
import io
import re

import colornames  # type: ignore
import discord
from PIL import Image, ImageDraw

from logic.jsonhandler import JsonHandler
from logic.tokengen import open_image_from_attachment, open_image_from_url
from methods import ChoicedEnum, FontType, get_font, when
import colorsys


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


async def save_image_color(itr: discord.Interaction, attachment: discord.Attachment | None) -> UserColorSaveResult:
    avatar = itr.user.display_avatar or itr.user.avatar
    if not avatar:
        raise RuntimeError("You don't have a profile picture set!")

    if not attachment:
        image = await open_image_from_url(avatar.url)
    else:
        image = await open_image_from_attachment(attachment)

    image = image.convert("RGB").resize((256, 256))
    quantized = image.quantize(colors=8, method=2)
    color_counts = quantized.getcolors()
    palette = quantized.getpalette()

    if not color_counts or not palette:
        raise ValueError("Could not retrieve colors from that image!")

    candidates: list[tuple[float, int, int]] = []  # (saturation, count, color_int)

    for count, index in color_counts:
        i: int = index * 3  # type: ignore
        r: int = palette[i]
        g: int = palette[i + 1]
        b: int = palette[i + 2]

        _, s, _ = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        color = discord.Color.from_rgb(r, g, b).value
        candidates.append((s, count, color))

    if not candidates:
        raise RuntimeError("Could not determine dominant colors.")

    # Prioritize by saturation first, then by frequency
    candidates.sort(key=lambda t: (t[0], t[1]), reverse=True)
    best_colors = [c for _, _, c in candidates[:5]]

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
