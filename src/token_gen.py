import io
import os
import time
import aiohttp
import discord
import numpy as np
from PIL import Image, ImageDraw


TOKEN_FRAME = Image.open("./img/token_border.png").convert("RGBA")


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


def _crop_image(
    image: Image.Image, max_size: tuple[int, int] = (512, 512), inset: int = 8
) -> Image.Image:
    """
    Processes the input image by:
    1. Cropping it to a square shape.
    2. Applying an inset, to make sure image fits within frame.
    3. Applying a white background, for cleaner transparent image handling.
    4. Applying a transparent circular mask to make the image round.
    """

    width_x = max_size[0]
    width_y = max_size[1]

    # Make square-shaped
    size = min(image.size)
    left = (image.width - size) / 2
    top = (image.height - size) / 2
    image = image.crop((left, top, left + size, top + size))

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


def get_hue_frame(hue: int) -> Image.Image:
    """
    Returns a copy of TOKEN_FRAME with its hue shifted by the given amount.
    Hue should be in the range -360 to 360.
    """
    if hue == 0:
        return TOKEN_FRAME.copy()

    # Convert to HSV, shift hue, and convert back
    frame = TOKEN_FRAME.convert("RGBA")
    r, g, b, a = frame.split()
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


def generate_token_image(image: Image.Image, hue: int) -> Image.Image:
    inner = _crop_image(image, TOKEN_FRAME.size)
    frame = get_hue_frame(hue) if hue else TOKEN_FRAME
    return Image.alpha_composite(inner, frame)


def _get_filename(name: str) -> str:
    return f"{name}_token_{int(time.time())}.png"


def generate_token_url_filename(url: str) -> str:
    url_hash = str(abs(hash(url)))
    return _get_filename(url_hash)


def generate_token_filename(base_image: discord.Attachment) -> str:
    filename = os.path.splitext(base_image.filename)[0]
    return _get_filename(filename)


def image_to_bytesio(image: Image.Image) -> io.BytesIO:
    output = io.BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return output
