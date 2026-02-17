import pytest
from pytest_benchmark.fixture import BenchmarkFixture
from utils import tokengen_setup

from logic.tokengen import AlignH, AlignV, generate_token_files


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
        return tokengen_setup(
            align_v=v_alignment,
            align_h=h_alignment,
        )

    benchmark.pedantic(  # type: ignore
        generate_token_files,
        setup=setup,
        rounds=16,
        warmup_rounds=1,
    )
