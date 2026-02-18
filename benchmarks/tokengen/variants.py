import pytest
from pytest_benchmark.fixture import BenchmarkFixture
from benchmarks.tokengen.tokengen_utils import tokengen_setup

from logic.tokengen import generate_token_files


@pytest.mark.parametrize(("variants"), [(1), (2), (3), (4), (5), (6), (7), (8), (9), (10)])
def test_tokengen_variants(benchmark: BenchmarkFixture, variants: int) -> None:
    def setup():
        return tokengen_setup(variants=variants)

    rounds = max(16 - variants, 5)
    benchmark.pedantic(generate_token_files, setup=setup, rounds=rounds, warmup_rounds=1)  # type: ignore
