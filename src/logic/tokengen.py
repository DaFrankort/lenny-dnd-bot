import io
import math
import os
import time
import aiohttp
import discord
import numpy as np
from PIL import Image, ImageDraw
from methods import ChoicedEnum, FontType, get_font

TOKEN_FRAME = Image.open("./assets/images/token_border.png").convert("RGBA")
TOKEN_BG = Image.open("./assets/images/token_bg.jpg").convert("RGBA")
TOKEN_NUMBER_LABEL = Image.open("./assets/images/token_number_label.png").convert("RGBA")
TOKEN_NUMBER_OVERLAY = Image.open("./assets/images/token_number_overlay.png").convert("RGBA")


class AlignH(str, ChoicedEnum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class AlignV(str, ChoicedEnum):
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


def _squarify_image(image: Image.Image, h_align: AlignH, v_align: AlignV) -> Image.Image:
    """Turn image into a square and adjust focus to match given alignment."""

    size = min(image.size)

    if h_align == AlignH.LEFT:
        left = 0
        right = size
    elif h_align == AlignH.RIGHT:
        left = image.width - size
        right = image.width
    else:
        left = (image.width - size) // 2
        right = left + size

    if v_align == AlignV.TOP:
        top = 0
        bottom = size
    elif v_align == AlignV.BOTTOM:
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
    image = image.resize((inner_width, inner_height), Image.Resampling.LANCZOS)

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


def generate_token_variants(
    token_image: Image.Image,
    filename_seed: discord.Attachment | str,
    amount: int,
) -> list[discord.File]:
    files: list[discord.File] = []
    for i in range(amount):
        id = i + 1
        labeled_image = add_number_to_tokenimage(token_image=token_image, number=id, amount=amount)
        filename = (
            generate_token_url_filename(filename_seed, id)
            if isinstance(filename_seed, str)
            else generate_token_filename(filename_seed, id)
        )
        files.append(
            discord.File(
                fp=image_to_bytesio(labeled_image),
                filename=filename,
            )
        )

    return files


def add_number_to_tokenimage(token_image: Image.Image, number: int, amount: int) -> Image.Image:
    label_size = (72, 72)
    font_size = int(min(label_size) * 0.6) if number < 10 else int(min(label_size) * 0.5)

    label = TOKEN_NUMBER_LABEL.copy()
    variant_hue = int((number - 1) * (360 / amount))
    overlay = _shift_hue(TOKEN_NUMBER_OVERLAY.copy(), variant_hue)
    label.alpha_composite(overlay)
    label = label.rotate(
        (number - 1) * (360 / amount + 1)
    )  # +1 So the last label does not have the same rotation as the first.
    label = label.resize(label_size)

    # Prepare text & font
    font = get_font(FontType.FANTASY, font_size)
    draw = ImageDraw.Draw(label)
    text = str(number)

    # Calculate label-center
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (label_size[0] - text_width) // 2
    y = (label_size[1] - text_height * 2) // 2

    if number == 7 and font.font.family and "merienda" in font.font.family.lower():
        y += (
            text_height // 6
        )  # Merienda's '7' is shifted upwards, thus requires compensation, dividing by 6 gave nicest results.

    # Draw text
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
    angle_deg = 90  # 90 Is bottom, 0 is right-side
    angle_rad = math.radians(angle_deg)

    # Token Center
    cx = token_image.width // 2
    cy = token_image.height // 2
    # Radius Adjustment
    rx = cx - (label.width // 2)
    ry = cy - (label.height // 2)
    # Rim position
    px = cx + int(rx * math.cos(angle_rad)) - (label.width // 2)
    py = cy + int(ry * math.sin(angle_rad)) - (label.height // 2)

    # Adjust to place label so its center is on the rim
    pos = (int(px), int(py))
    combined = token_image.copy()
    combined.alpha_composite(label, dest=pos)

    return combined


async def generate_token_from_file(
    image: discord.Attachment,
    frame_hue: int,
    h_alignment: AlignH,
    v_alignment: AlignV,
    variants: int,
) -> list[discord.File]:
    if not image.content_type:
        raise ValueError("Unknown attachment type!")
    if not image.content_type.startswith("image"):
        raise ValueError("Attachment must be an image.")

    img = await open_image(image)
    if img is None:
        raise ValueError("Could not process image, please try again later or with another image.")

    token_image = generate_token_image(img, frame_hue, h_alignment, v_alignment)

    if variants != 0:
        files = generate_token_variants(token_image=token_image, filename_seed=image, amount=variants)
        return files
    file = discord.File(fp=image_to_bytesio(token_image), filename=generate_token_filename(image))
    return [file]


async def generate_token_from_url(
    url: str, frame_hue: int, h_alignment: AlignH, v_alignment: AlignV, variants: int
) -> list[discord.File]:
    if not url.startswith("http"):
        raise ValueError(f"Not a valid URL: '{url}'")

    img = await open_image_url(url)
    if img is None:
        raise ValueError("Could not process image, please provide a valid image-URL.")

    token_image = generate_token_image(img, frame_hue, h_alignment, v_alignment)

    if variants != 0:
        files = generate_token_variants(token_image=token_image, filename_seed=url, amount=variants)
        return files
    file = discord.File(fp=image_to_bytesio(token_image), filename=generate_token_url_filename(url))
    return [file]
