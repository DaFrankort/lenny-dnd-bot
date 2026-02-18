from test.mocking import ExternalAsset

import pytest
from benchmarks.tokengen.tokengen_utils import tokengen_setup
from pytest_benchmark.fixture import BenchmarkFixture

from logic.tokengen import AlignH, AlignV, generate_token_files, open_image_from_url


@pytest.mark.parametrize(
    ("v_alignment", "h_alignment"),
    [
        (AlignV.TOP, AlignH.FACE),
        (AlignV.TOP, AlignH.FACE),
        (AlignV.TOP, AlignH.FACE),
        (AlignV.FACE, AlignH.LEFT),
        (AlignV.FACE, AlignH.CENTER),
        (AlignV.FACE, AlignH.RIGHT),
        (AlignV.FACE, AlignH.FACE),
    ],
)
async def test_tokengen_align_face(
    benchmark: BenchmarkFixture,
    v_alignment: AlignV,
    h_alignment: AlignH,
) -> None:
    """Benchmark all alignment combinations separately"""
    image = await open_image_from_url(ExternalAsset.IMAGE_FACE.value)

    def setup():
        return tokengen_setup(
            image=image,
            align_v=v_alignment,
            align_h=h_alignment,
        )

    benchmark.pedantic(  # type: ignore
        generate_token_files,
        setup=setup,
        rounds=32,
        warmup_rounds=4,
    )
