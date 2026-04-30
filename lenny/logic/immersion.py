import io
import math
import random
from enum import Enum

import d20.utils
import discord
from PIL import Image, ImageDraw, ImageFont

from logic.color import UserColor, get_luminance_font_color
from logic.roll import RollResult


class DiceType(Enum):
    D4 = "d4"
    D6 = "d6"
    D8 = "d8"
    D10 = "d10"
    D12 = "d12"
    D20 = "d20"


def size_to_dice_type(size: int | str) -> DiceType:
    return {
        4: DiceType.D4,
        6: DiceType.D6,
        8: DiceType.D8,
        10: DiceType.D10,
        12: DiceType.D12,
        20: DiceType.D20,
        "%": DiceType.D10,
    }.get(size, DiceType.D20)


def generate_dice_image(
    itr: discord.Interaction,
    results: list[RollResult],
    canvas_size: tuple[int, int] = (240, 240),
) -> discord.File:
    rgb = discord.Color(UserColor.get(itr)).to_rgb()

    canvas = Image.new(
        "RGBA",
        canvas_size,
        (0, 0, 0, 0),
    )
    width, height = canvas_size

    for result in results:
        types: list[tuple[DiceType, int, tuple[int, int, int]]] = []
        for roll in result.result.rolls:
            color = (100, 100, 100)
            if roll == result.result.roll:
                color = rgb

            rolled_dice = d20.utils.extract_dice(roll.roll)
            for rolled_die in rolled_dice:
                die_type = size_to_dice_type(rolled_die.size)
                types.append((die_type, rolled_die.value, color))

        for die_type, value, color in types:
            die_img = get_die_icon(
                die_type=die_type,
                value=value,
                rgb=color,
                size=80,
            )

            rotated = die_img.rotate(
                random.randint(0, 359),
                expand=True,
                resample=Image.Resampling.BICUBIC,
            )

            rw, rh = rotated.size

            # Keep fully inside canvas
            max_x = max(0, width - rw)
            max_y = max(0, height - rh)

            x = random.randint(0, max_x)
            y = random.randint(0, max_y)

            canvas.paste(rotated, (x, y), rotated)

    buffer = io.BytesIO()
    canvas.save(buffer, format="PNG")
    buffer.seek(0)

    return discord.File(
        fp=buffer,
        filename="dice_roll.png",
    )


def adjust_color(rgb: tuple[int, int, int], factor: float):
    return tuple(max(0, min(255, int(channel * factor))) for channel in rgb)


def regular_polygon(
    center: tuple[int, int],
    radius: int,
    sides: int,
    rotation: float = 0,
):
    cx, cy = center
    points: list[tuple[float, float]] = []

    for i in range(sides):
        angle = math.radians((360 / sides) * i + rotation)
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        points.append((x, y))
    return points


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    size: int,
    canvas_size: int,
    fill: tuple[int, int, int],
):
    try:
        font = ImageFont.truetype("arial.ttf", size)
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)

    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (canvas_size - text_width) / 2
    y = (canvas_size - text_height) / 2 - 2

    draw.text((x, y), text, fill=fill, font=font)

    if text in ("6", "9"):
        underline_y = y + (text_height * 1.5)
        padding = 2
        draw.line((x + padding, underline_y, x + text_width - padding, underline_y), fill=fill, width=4)


def get_die_icon(die_type: DiceType, value: int, rgb: tuple[int, int, int], size: int = 256) -> Image.Image:
    font = get_luminance_font_color(rgb)

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    center = (size // 2, size // 2)
    radius = size // 3

    if die_type == DiceType.D4:
        points = regular_polygon(center, radius, 3, rotation=-90)

    elif die_type == DiceType.D6:
        points = regular_polygon(center, radius, 4, rotation=30)

    elif die_type == DiceType.D8:
        points = [
            (center[0], 28),
            (size - 36, center[1]),
            (center[0], size - 28),
            (36, center[1]),
        ]

    elif die_type == DiceType.D10:
        points = regular_polygon(center, radius, 5, rotation=-90)

    elif die_type == DiceType.D12:
        points = regular_polygon(center, radius, 6, rotation=30)

    elif die_type == DiceType.D20:
        points = regular_polygon(center, radius, 8, rotation=22)

    else:
        raise ValueError(f"Unsupported die type: {die_type}")

    draw.polygon(points, fill=rgb, outline=font, width=4)  # Main

    draw_centered_text(
        draw=draw,
        text=str(value),
        size=size // 4,
        canvas_size=size,
        fill=font,
    )

    return img
