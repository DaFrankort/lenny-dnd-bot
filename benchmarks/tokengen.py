import pytest
from PIL import Image
from pytest_benchmark.fixture import BenchmarkFixture

from logic.tokengen import AlignH, AlignV, generate_token_files


def _tokengen_setup(
    image: Image.Image | None = None,
    name: str = "benchmark",
    hue_shift: int = 0,
    align_h: AlignH = AlignH.CENTER,
    align_v: AlignV = AlignV.CENTER,
    variants: int = 1,
    background: Image.Image | None = None,
) -> tuple[tuple[object], dict[object, object]]:
    image = image or Image.new("RGBA", (512, 512), (255, 0, 0, 255))
    background = background or Image.new("RGBA", (512, 512), (0, 0, 0, 0))
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


def test_generate_token_basic(benchmark: BenchmarkFixture) -> None:
    """Generate a simple token with default options"""

    benchmark.pedantic(generate_token_files, setup=_tokengen_setup, rounds=64, warmup_rounds=4)  # type: ignore


def test_generate_token_shift_hue(benchmark: BenchmarkFixture) -> None:
    """Generate a simple token with a different frame-hue"""

    def setup():
        return _tokengen_setup(hue_shift=180)

    benchmark.pedantic(generate_token_files, setup=setup, rounds=64, warmup_rounds=4)  # type: ignore


@pytest.mark.parametrize(
    ("v_alignment", "h_alignment"),
    [
        (AlignV.TOP, AlignH.LEFT),
        (AlignV.TOP, AlignH.CENTER),
        (AlignV.TOP, AlignH.RIGHT),
        (AlignV.CENTER, AlignH.LEFT),
        (AlignV.CENTER, AlignH.CENTER),
        (AlignV.CENTER, AlignH.RIGHT),
        (AlignV.BOTTOM, AlignH.LEFT),
        (AlignV.BOTTOM, AlignH.CENTER),
        (AlignV.BOTTOM, AlignH.RIGHT),
    ],
)
def test_generate_token_basic_alignments(
    benchmark: BenchmarkFixture,
    v_alignment: AlignV,
    h_alignment: AlignH,
) -> None:
    """Benchmark all alignment combinations separately"""

    def setup():
        return _tokengen_setup(
            align_v=v_alignment,
            align_h=h_alignment,
        )

    benchmark.pedantic(  # type: ignore
        generate_token_files,
        setup=setup,
        rounds=16,
        warmup_rounds=1,
    )
