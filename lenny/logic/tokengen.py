import io
import logging
import math
import os
import time
from collections.abc import Sequence

import aiohttp
import cv2
import discord
import numpy as np
from PIL import Image, ImageDraw, UnidentifiedImageError

from methods import ChoicedEnum, FontType, get_font

TOKEN_FRAME = Image.open("./assets/images/token_border.png").convert("RGBA")
TOKEN_BG = Image.open("./assets/images/token_bg.jpg").convert("RGBA")
TOKEN_NUMBER_LABEL = Image.open("./assets/images/token_number_label.png").convert("RGBA")
TOKEN_NUMBER_OVERLAY = Image.open("./assets/images/token_number_overlay.png").convert("RGBA")
CASCADES = tuple(
    # pylint: disable=no-member
    cv2.CascadeClassifier(filename=cv2.data.haarcascades + model)  # type: ignore
    for model in (
        "haarcascade_frontalface_alt2.xml",  # Best balance
        "haarcascade_frontalface_default.xml",  # Backup
        "haarcascade_profileface.xml",  # For "cool guy looking away" portraits
        "haarcascade_frontalcatface_extended.xml",  # Feline-like races and animals
        "haarcascade_eye.xml",  # Fallback for less human-like faces
        "haarcascade_fullbody.xml",  # Find center of the whole person instead
    )
)


class AlignH(str, ChoicedEnum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    DETECT = "detect"


class AlignV(str, ChoicedEnum):
    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"
    DETECT = "detect"


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
    except UnidentifiedImageError as exc:
        logging.error(exc)
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


def _detect_face_center(image: Image.Image) -> tuple[int, int]:
    img = np.array(image.convert("RGB"))

    # pylint: disable=no-member
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    faces: Sequence[tuple[int, int, int, int]] = ()
    for cascade in CASCADES:
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))  # type: ignore
        if len(faces) != 0:
            break

    if len(faces) == 0:
        raise ValueError("Failed to detect any facial features on that image, please adjust manually instead.")

    # largest face
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    return (x + w // 2, y + h // 2)


def _squarify_image(image: Image.Image, h_align: AlignH, v_align: AlignV) -> Image.Image:
    """Turn image into a square and adjust focus to match given alignment."""

    size = min(image.size)
    face: tuple[int, int] | tuple[None, None] = (None, None)
    if h_align == AlignH.DETECT or v_align == AlignV.DETECT:
        face = _detect_face_center(image)

    if h_align == AlignH.LEFT:
        left = 0
        right = size
    elif h_align == AlignH.RIGHT:
        left = image.width - size
        right = image.width
    elif h_align == AlignH.DETECT and face[0]:
        left = face[0] - (size // 2)
        left = max(0, min(left, image.width - size))
        right = left + size
    else:
        left = (image.width - size) // 2
        right = left + size

    if v_align == AlignV.TOP:
        top = 0
        bottom = size
    elif v_align == AlignV.BOTTOM:
        top = image.height - size
        bottom = image.height
    elif v_align == AlignV.DETECT and face[1]:
        top = face[1] - (size // 2)
        top = max(0, min(top, image.height - size))
        bottom = top + size
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


def _get_filename(name: str, token_id: int) -> str:
    return f"{name}_token_{int(time.time())}_{token_id}.png"


def generate_token_url_filename(url: str, token_id: int = 0) -> str:
    url_hash = str(abs(hash(url)))
    return _get_filename(url_hash, token_id)


def generate_token_filename(base_image: discord.Attachment, token_id: int = 0) -> str:
    filename = os.path.splitext(base_image.filename)[0]
    return _get_filename(filename, token_id)


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
        token_id = i + 1
        labeled_image = add_number_to_tokenimage(token_image=token_image, number=token_id, amount=amount)
        filename = (
            generate_token_url_filename(filename_seed, token_id)
            if isinstance(filename_seed, str)
            else generate_token_filename(filename_seed, token_id)
        )
        files.append(
            discord.File(
                fp=image_to_bytesio(labeled_image),
                filename=filename,
            )
        )

    return files


def calculate_number_position_of_token_image(
    token_image: Image.Image,
    label: Image.Image,
    angle_rad: float,
) -> tuple[int, int]:
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
    return (int(px), int(py))


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
        # Merienda's '7' is shifted upwards, thus requires compensation, dividing by 6 gave nicest results.
        y += text_height // 6

    # Draw text
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
    angle_rad = math.radians(90)  # 90 Is bottom, 0 is right-side

    # Adjust to place label so its center is on the rim
    pos = calculate_number_position_of_token_image(token_image, label, angle_rad)

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
