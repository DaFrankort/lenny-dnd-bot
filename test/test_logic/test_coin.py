import pytest

from logic.coin import Coin


def assert_coin(expression: str, coin: Coin, expected: Coin):
    assert coin.pp == expected.pp, f"{expression} | PP => {coin} != {expected}"
    assert coin.gp == expected.gp, f"{expression} | GP => {coin} != {expected}"
    assert coin.ep == expected.ep, f"{expression} | EP => {coin} != {expected}"
    assert coin.sp == expected.sp, f"{expression} | SP => {coin} != {expected}"
    assert coin.cp == expected.cp, f"{expression} | CP => {coin} != {expected}"


class TestCoin:

    @pytest.mark.parametrize(
        "expression, expected_result",
        [
            ("5cp + 5cp", Coin(sp=1)),
            ("2sp + 5cp + 2sp + 5cp", Coin(ep=1)),
            ("5sp + 5sp", Coin(gp=1)),
            ("1ep + 1ep", Coin(gp=1)),
            ("5gp + 5gp", Coin(pp=1)),
            ("10gp + 5gp", Coin(pp=1, gp=5)),
            ("1gp 1ep + 1ep", Coin(gp=2)),
            ("1ep + 1gp 1ep", Coin(gp=2)),
            ("(1gp + 1ep) + 1ep", Coin(gp=2)),
            ("1ep + (1gp + 1ep)", Coin(gp=2)),
        ],
    )
    def test_addition(self, expression: str, expected_result: Coin):
        coin = Coin.from_string(expression)
        assert_coin(expression, coin, expected_result)

    @pytest.mark.parametrize(
        "expression, expected_result",
        [
            ("100gp 50cp - 50cp", Coin(pp=10)),
            ("10pp - 5gp", Coin(pp=9, gp=5)),
            ("5gp - 25cp", Coin(gp=4, sp=7, cp=5)),
            ("1gp - 5cp", Coin(sp=9, cp=5)),
            ("1ep - 5cp", Coin(cp=5)),
            ("1gp 5sp - 5sp", Coin(gp=1)),
            ("2gp 5sp - 5sp", Coin(gp=2)),
            ("(2gp + 5sp) - 5sp", Coin(gp=2)),
            ("10gp - (2gp + 5gp)", Coin(gp=3)),
        ],
    )
    def test_subtraction(self, expression: str, expected_result: Coin):
        coin = Coin.from_string(expression)
        assert_coin(expression, coin, expected_result)

    @pytest.mark.parametrize(
        "expression, expected_result",
        [
            ("5gp * 2", Coin(pp=1)),
            ("15gp * 2", Coin(pp=3)),
            ("2pp * 3", Coin(pp=6)),
            ("5sp * 2", Coin(gp=1)),
            ("5cp * 2", Coin(sp=1)),
            ("10gp * 1.5", Coin(pp=1, gp=5)),
            ("1pp * 1.5", Coin(pp=1, gp=5)),
            ("2gp * 2.5", Coin(gp=5)),
            ("4sp * 1.5", Coin(sp=6)),
            ("10cp * 1.5", Coin(sp=1, cp=5)),
            ("(5gp + 5gp) * 1.5", Coin(pp=1, gp=5)),
        ],
    )
    def test_multiplication(self, expression: str, expected_result: Coin):
        coin = Coin.from_string(expression)
        assert_coin(expression, coin, expected_result)

    @pytest.mark.parametrize(
        "expression, expected_result",
        [
            ("10gp / 2", Coin(gp=5)),
            ("1pp / 2", Coin(gp=5)),
            ("3pp / 2", Coin(pp=1, gp=5)),
            ("1gp / 2", Coin(sp=5)),
            ("1sp / 2", Coin(cp=5)),
            ("15gp / 1.5", Coin(pp=1)),
            ("1pp / 4", Coin(sp=25)),
            ("5gp / 2", Coin(gp=2, sp=5)),
            ("3sp / 1.5", Coin(sp=2)),
            ("15cp / 1.5", Coin(sp=1)),
            ("(10gp + 5gp) / 3", Coin(gp=5)),
        ],
    )
    def test_division(self, expression: str, expected_result: Coin):
        coin = Coin.from_string(expression)
        assert_coin(expression, coin, expected_result)
