from test.mocking import ExternalAsset

import pytest
from benchmarks.tokengen.tokengen_utils import tokengen_setup
from pytest_benchmark.fixture import BenchmarkFixture

from logic.tokengen import BackgroundType, generate_token_files, open_image_from_url


def test_tokengen_simple(benchmark: BenchmarkFixture) -> None:
    benchmark.pedantic(generate_token_files, setup=tokengen_setup, rounds=64, warmup_rounds=4)  # type: ignore


def test_tokengen_shift_hue(benchmark: BenchmarkFixture) -> None:
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
async def test_tokengen_transparent_image_with_bg(benchmark: BenchmarkFixture, bg_type: BackgroundType) -> None:
    image = await open_image_from_url(ExternalAsset.IMAGE.value)

    def setup():
        return tokengen_setup(image=image, background=bg_type.image)

    benchmark.pedantic(generate_token_files, setup=setup, rounds=64, warmup_rounds=4)  # type: ignore


async def test_tokengen_custom_bg(benchmark: BenchmarkFixture) -> None:
    image = await open_image_from_url(ExternalAsset.IMAGE.value)
    background = await open_image_from_url(ExternalAsset.BACKGROUND.value)

    def setup():
        return tokengen_setup(image=image, background=background)

    benchmark.pedantic(generate_token_files, setup=setup, rounds=64, warmup_rounds=4)  # type: ignore
