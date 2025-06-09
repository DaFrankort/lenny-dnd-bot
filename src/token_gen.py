import io
import os
import time
import aiohttp
import discord
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


def generate_token_image(image: Image.Image) -> Image.Image:
    inner = _crop_image(image, TOKEN_FRAME.size)
    return Image.alpha_composite(inner, TOKEN_FRAME)


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
