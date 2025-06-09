import io
import aiohttp
import discord
from PIL import Image, ImageDraw


TOKEN_FRAME = Image.open("./img/token_border.png").convert("RGBA")


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
    2. Resizing it with an inset so it fits within max_size.
    3. Applying a transparent circular mask to make the image round.
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
