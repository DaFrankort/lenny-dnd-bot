from enum import Enum
import io
import math
import os
import time
import aiohttp
import discord
import numpy as np
from PIL import Image, ImageDraw, ImageFont


TOKEN_FRAME = Image.open("./assets/images/token_border.png").convert("RGBA")
TOKEN_BG = Image.open("./assets/images/token_bg.jpg").convert("RGBA")


class AlignH(Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class AlignV(Enum):
    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"


async def open_image_url(url: str) -> Image.Image | None:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            content_type = resp.headers.get("Content-Type", "")
            if not content_type.startswith("image/"):
                return None
            image_bytes = await resp.read()

    try:
        base_image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    except Exception:
        return None

    return base_image


async def open_image(image: discord.Attachment) -> Image.Image | None:
    async with aiohttp.ClientSession() as session:
        async with session.get(image.url) as resp:
            if resp.status != 200:
                return None
            image_bytes = await resp.read()

    base_image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

    if not base_image:
        return None

    return base_image


def _squarify_image(
    image: Image.Image, h_align: AlignH, v_align: AlignV
) -> Image.Image:
    """Turn image into a square and adjust focus to match given alignment."""

    size = min(image.size)

    if h_align == AlignH.LEFT.value:
        left = 0
        right = size
    elif h_align == AlignH.RIGHT.value:
        left = image.width - size
        right = image.width
    else:
        left = (image.width - size) // 2
        right = left + size

    if v_align == AlignV.TOP.value:
        top = 0
        bottom = size
    elif v_align == AlignV.BOTTOM.value:
        top = image.height - size
        bottom = image.height
    else:
        top = (image.height - size) // 2
        bottom = top + size

    image = image.crop((left, top, right, bottom))
    return image


def _crop_image(
    image: Image.Image,
    h_align: AlignH,
    v_align: AlignV,
    max_size: tuple[int, int] = (512, 512),
    inset: int = 8,
) -> Image.Image:
    """
    Processes the input image by:
    1. Cropping it to a square shape, adjusting the focus of the image.
    2. Applying an inset, to make sure image fits within frame.
    3. Applying a white background, for cleaner transparent image handling.
    4. Applying a transparent circular mask to make the image round.
    """

    width_x = max_size[0]
    width_y = max_size[1]

    # Make square-shaped
    image = _squarify_image(image, h_align, v_align)

    # Resize with inset to avoid sticking out of the frame
    inner_width = width_x - 2 * inset
    inner_height = width_y - 2 * inset
    image = image.resize((inner_width, inner_height), Image.LANCZOS)

    # Add white background, for cleaner png-tokens
    white_bg = Image.new("RGBA", image.size, (255, 255, 255, 255))
    white_bg.paste(image, (0, 0), image)
    image = white_bg

    # Apply circular mask
    mask = Image.new("L", (inner_width, inner_height), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, inner_width, inner_height), fill=255)
    image.putalpha(mask)

    # Paste onto transparent background of full token size
    background = Image.new("RGBA", (width_x, width_y), (0, 0, 0, 0))
    background.paste(image, (inset, inset), image)
    return background


def _shift_hue(image: Image.Image, hue: int) -> Image.Image:
    """
    Returns a copy of an image with its hue shifted by the given amount.
    Hue should be in the range -360 to 360.
    """
    if hue == 0:
        return image.copy()

    # Convert to HSV, shift hue, and convert back
    r, g, b, a = image.split()
    rgb_image = Image.merge("RGB", (r, g, b))
    hsv_image = rgb_image.convert("HSV")
    h, s, v = hsv_image.split()

    # Calculate hue shift in 0-255 scale
    hue_shift = int((hue % 360) * 255 / 360)
    np_h = np.array(h, dtype=np.uint8).astype(np.uint16)
    np_h = (np_h + hue_shift) % 256
    np_h = np_h.astype(np.uint8)
    h = Image.fromarray(np_h, "L")

    shifted_hsv = Image.merge("HSV", (h, s, v))
    shifted_rgb = shifted_hsv.convert("RGB")
    shifted_rgba = Image.merge("RGBA", (*shifted_rgb.split(), a))
    return shifted_rgba


def generate_token_image(
    image: Image.Image,
    hue: int,
    h_align: AlignH = AlignH.CENTER,
    v_align: AlignV = AlignV.CENTER,
) -> Image.Image:
    inner = _crop_image(image, h_align, v_align, TOKEN_FRAME.size)
    frame = _shift_hue(TOKEN_FRAME, hue)
    return Image.alpha_composite(inner, frame)


def _get_filename(name: str, id: int) -> str:
    return f"{name}_token_{int(time.time())}_{id}.png"


def generate_token_url_filename(url: str, id: int = 0) -> str:
    url_hash = str(abs(hash(url)))
    return _get_filename(url_hash, id)


def generate_token_filename(base_image: discord.Attachment, id: int = 0) -> str:
    filename = os.path.splitext(base_image.filename)[0]
    return _get_filename(filename, id)


def image_to_bytesio(image: Image.Image) -> io.BytesIO:
    output = io.BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return output


def generate_token_variants(token_image: Image.Image, attachment: discord.Attachment, amount: int, hue: int) -> list[discord.File]:
    files = []
    for i in range(amount):
        id = i + 1
        labeled_image = add_number_to_tokenimage(
            token_image=token_image, number=id, amount=amount, hue=hue
        )
        files.append(
            discord.File(
                fp=image_to_bytesio(labeled_image),
                filename=generate_token_filename(attachment, id),
            )
        )

    return files

def add_number_to_tokenimage(
    token_image: Image.Image, number: int, amount: int, hue: int
) -> Image.Image:
    # Create label
    label_size = (48, 48)
    font_size = int(label_size[1] * 0.8)

    frame = TOKEN_FRAME.copy()
    frame = frame.resize(label_size, Image.LANCZOS)
    bg_hue = ((number - 1) * (360 / amount)) - hue
    bg = _shift_hue(TOKEN_BG, bg_hue)
    bg = _crop_image(
        bg, h_align=AlignH.CENTER, v_align=AlignV.CENTER, max_size=label_size, inset=2
    )
    label = Image.alpha_composite(bg, frame)

    # Prepare text & font
    try:
        font = ImageFont.truetype("./assets/fonts/Merienda-Black.ttf", font_size)
    except OSError:
        font = ImageFont.load_default(font_size)

    draw = ImageDraw.Draw(label)
    text = str(number)

    # Calculate center
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (label_size[0] - text_width) // 2
    y = (label_size[1] - text_height * 2) // 2

    # Draw text
    draw.text((x, y), text, font=font, fill=(255, 255, 200, 255))
    label = _shift_hue(label, hue)

    # Add label to token_image
    pos = (
        int(token_image.width - frame.width) // 2,
        int(token_image.height - frame.height),
    )
    combined = token_image.copy()
    combined.alpha_composite(label, dest=pos)

    return combined
