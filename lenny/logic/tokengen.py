import io
import math
import os
import time
from collections.abc import Sequence
from typing import Literal

import aiohttp
import cv2
import discord
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageSequence

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
EXPORTABLE_EXTENSIONS = Literal["PNG", "WEBP"]


class AlignH(str, ChoicedEnum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    FACE = "detect face"


class AlignV(str, ChoicedEnum):
    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"
    FACE = "detect face"


class BackgroundType(str, ChoicedEnum):
    FANCY = "fancy"
    WHITE = "white"
    TRANSPARENT = "transparent"


async def open_image_from_url(url: str) -> Image.Image:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise ValueError(f"Could not open image url: {url}")

            content_type = resp.headers.get("Content-Type", "")
            if not content_type.startswith("image/"):
                raise ValueError("Could not process image, please provide a URL that links to a valid image.")

            image_bytes = await resp.read()

    return Image.open(io.BytesIO(image_bytes))


async def open_image_from_attachment(image: discord.Attachment) -> Image.Image:
    async with aiohttp.ClientSession() as session:
        async with session.get(image.url) as resp:
            if resp.status != 200:
                raise ValueError(f"Could not open image url: {image.url}")
            image_bytes = await resp.read()

    base_image = Image.open(io.BytesIO(image_bytes))

    if not base_image:
        raise ValueError("Could not process image, please provide a valid image file.")

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
    if h_align == AlignH.FACE or v_align == AlignV.FACE:
        face = _detect_face_center(image)

    if h_align == AlignH.LEFT:
        left = 0
        right = size
    elif h_align == AlignH.RIGHT:
        left = image.width - size
        right = image.width
    elif h_align == AlignH.FACE and face[0]:
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
    elif v_align == AlignV.FACE and face[1]:
        top = face[1] - (size // 2)
        top = max(0, min(top, image.height - size))
        bottom = top + size
    else:
        top = (image.height - size) // 2
        bottom = top + size

    image = image.crop((left, top, right, bottom))
    return image


def _apply_background(
    image: Image.Image,
    bg_type: BackgroundType,
) -> Image.Image:
    if bg_type.value == BackgroundType.TRANSPARENT.value:
        bg = Image.new("RGBA", image.size, (0, 0, 0, 0))

    elif bg_type.value == BackgroundType.WHITE.value:
        bg = Image.new("RGBA", image.size, (255, 255, 255, 255))

    elif bg_type.value == BackgroundType.FANCY.value:
        bg = TOKEN_BG.copy().resize(image.size)

    else:
        raise ValueError(f"Unknown background-type: {bg_type.name.title()}")

    bg.paste(image, (0, 0), image)
    return bg


def _crop_image(
    image: Image.Image,
    h_align: AlignH,
    v_align: AlignV,
    size: tuple[int, int],
    inset: int = 8,
):
    width, height = size

    # Make square-shaped
    image = _squarify_image(image, h_align, v_align)

    # Resize with inset to avoid sticking out of the frame
    inner_width = width - 2 * inset
    inner_height = height - 2 * inset
    return image.resize((inner_width, inner_height), Image.Resampling.LANCZOS)


def _apply_circular_mask(
    image: Image.Image,
    bg_type: BackgroundType,
    size: tuple[int, int],
    inset: int = 8,
):
    width, height = size
    inner_width = width - 2 * inset
    inner_height = height - 2 * inset

    mask = Image.new("L", (inner_width, inner_height), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, inner_width, inner_height), fill=255)

    # Adjust alpha channels
    alpha = mask
    if bg_type is BackgroundType.TRANSPARENT:
        # If the background is transparent, we want to retain the transparency of the original image.
        # With a solid background we don't want this, because it gives an odd effect where the main image transparency is retained over the background.
        original_alpha = image.getchannel("A")
        alpha = ImageChops.multiply(original_alpha, mask)
    image.putalpha(alpha)

    result = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    result.paste(image, (inset, inset), image)
    return result


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


def _generate_token_image(
    image: Image.Image,
    hue: int,
    bg_type: BackgroundType,
    h_align: AlignH,
    v_align: AlignV,
) -> list[Image.Image]:
    frames: list[Image.Image] = []

    border = _shift_hue(TOKEN_FRAME, hue)
    size = TOKEN_FRAME.size

    for frame in ImageSequence.Iterator(image):
        frame = frame.convert("RGBA")
        frame = _crop_image(frame, h_align, v_align, size)
        frame = _apply_background(frame, bg_type)
        frame = _apply_circular_mask(frame, bg_type, size)
        frames.append(Image.alpha_composite(frame, border))

    return frames


def _get_filename(name: str, extension: str, token_id: int) -> str:
    return f"{name}_token_{int(time.time())}_{token_id}.{extension}"


def _image_to_bytesio(image: list[Image.Image], file_format: EXPORTABLE_EXTENSIONS, duration: int = 0) -> io.BytesIO:
    output = io.BytesIO()
    print(file_format, duration)

    if file_format == "PNG":
        image[0].save(output, format=file_format)

    elif file_format == "WEBP":
        image[0].save(
            output,
            format="WEBP",
            save_all=True,
            append_images=image[1:],
            duration=duration,
            loop=0,
            lossless=False,  # Set to True for higher quality/larger file
            quality=80,
        )

    output.seek(0)
    return output


def _calculate_number_position_of_token_image(
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
    return int(px), int(py)


def _add_number_to_tokenimage(token_image: Image.Image, number: int, amount: int) -> Image.Image:
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
    pos = _calculate_number_position_of_token_image(token_image, label, angle_rad)

    combined = token_image.copy()
    combined.alpha_composite(label, dest=pos)

    return combined


async def _generate_token_files(
    image: Image.Image,
    name: str,
    frame_hue: int,
    h_alignment: AlignH,
    v_alignment: AlignV,
    variants: int,
    bg_type: BackgroundType,
) -> list[discord.File]:
    base_token = _generate_token_image(image, frame_hue, bg_type, h_alignment, v_alignment)

    extension: EXPORTABLE_EXTENSIONS = "PNG"
    duration: int = 0
    if len(base_token) > 1:
        extension = "WEBP"
        duration = image.info["duration"] if "duration" in image.info else 40

    # If only a single image, and no variants, return as-is
    if variants <= 0:
        filename = _get_filename(name, extension, 0)
        return [discord.File(_image_to_bytesio(base_token, extension, duration), filename)]

    raise NotImplementedError("Sorry! Still working on this!")

    # Otherwise, add variants
    files: list[discord.File] = []
    for i in range(variants):
        token_id = i + 1
        labeled_token = _add_number_to_tokenimage(base_token, token_id, variants)
        filename = _get_filename(name, extension, token_id)
        files.append(discord.File(_image_to_bytesio(labeled_token, extension), filename))

    return files


async def generate_tokens_from_file(
    image: discord.Attachment,
    frame_hue: int,
    h_alignment: AlignH,
    v_alignment: AlignV,
    variants: int,
    bg_type: BackgroundType,
) -> list[discord.File]:
    if not image.content_type:
        raise ValueError("Unknown attachment type!")
    if not image.content_type.startswith("image"):
        raise ValueError("Attachment must be an image.")

    img = await open_image_from_attachment(image)
    name = os.path.splitext(image.filename)[0]

    return await _generate_token_files(
        image=img,
        name=name,
        frame_hue=frame_hue,
        h_alignment=h_alignment,
        v_alignment=v_alignment,
        variants=variants,
        bg_type=bg_type,
    )


async def generate_tokens_from_url(
    url: str,
    frame_hue: int,
    h_alignment: AlignH,
    v_alignment: AlignV,
    variants: int,
    bg_type: BackgroundType,
) -> list[discord.File]:
    if not url.startswith("http"):
        raise ValueError(f"Not a valid URL: '{url}'")

    img = await open_image_from_url(url)
    url_hash = str(abs(hash(url)))

    return await _generate_token_files(
        image=img,
        name=url_hash,
        frame_hue=frame_hue,
        h_alignment=h_alignment,
        v_alignment=v_alignment,
        variants=variants,
        bg_type=bg_type,
    )
