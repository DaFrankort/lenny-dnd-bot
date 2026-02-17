from test.mocking import ExternalAsset

import pytest
from pytest_benchmark.fixture import BenchmarkFixture
from utils import tokengen_setup

from logic.tokengen import BackgroundType, generate_token_files, open_image_from_url


def test_generate_token_simple(benchmark: BenchmarkFixture) -> None:
    benchmark.pedantic(generate_token_files, setup=tokengen_setup, rounds=64, warmup_rounds=4)  # type: ignore


def test_generate_token_shift_hue(benchmark: BenchmarkFixture) -> None:
    def setup():
        return tokengen_setup(hue_shift=180)

    benchmark.pedantic(generate_token_files, setup=setup, rounds=64, warmup_rounds=4)  # type: ignore


@pytest.mark.parametrize(
    ("bg_type"),
    [
        (BackgroundType.FANCY),
        (BackgroundType.WHITE),
        (BackgroundType.TRANSPARENT),
    ],
)
async def test_generate_transparent_image_with_bg(benchmark: BenchmarkFixture, bg_type: BackgroundType) -> None:
    image = await open_image_from_url(ExternalAsset.IMAGE.value)

    def setup():
        return tokengen_setup(image=image, background=bg_type.image)

    benchmark.pedantic(generate_token_files, setup=setup, rounds=64, warmup_rounds=4)  # type: ignore
