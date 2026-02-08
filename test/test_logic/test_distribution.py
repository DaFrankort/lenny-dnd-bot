from approx import approx

from logic.distribution import distribution
from logic.roll import Advantage


class TestDistribution:
    def test_basic_d20(self):
        dist = distribution("d20", advantage=Advantage.NORMAL, color=0xFF00FF)

        assert dist.min == approx(1.0)
        assert dist.max == approx(20)
        assert dist.mean == approx(10.50)

    def test_d20_out_of_bounds(self):
        dist = distribution("1d20mi21", advantage=Advantage.NORMAL, color=0xFF00FF)

        assert dist.min == approx(21)
        assert dist.max == approx(21)
        assert dist.mean == approx(21)
        assert dist.stdev == approx(0.0)
