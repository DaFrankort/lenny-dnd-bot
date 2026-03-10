from PIL import Image

from logic.tokengen import AlignH, AlignV, BackgroundType


def tokengen_setup(
    image: Image.Image | None = None,
    name: str = "benchmark",
    hue_shift: int = 0,
    align_h: AlignH = AlignH.CENTER,
    align_v: AlignV = AlignV.CENTER,
    variants: int = 1,
    background: Image.Image = BackgroundType.FANCY.image,
) -> tuple[tuple[object], dict[object, object]]:
    image = image or Image.new("RGBA", (512, 512), (255, 0, 0, 255))
    return (
        (
            image,
            name,
            hue_shift,
            align_h,
            align_v,
            variants,
            background,
        ),  # type: ignore
        {},
    )
