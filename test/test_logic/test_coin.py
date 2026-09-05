import pytest

from logic.coin import Coin, parse_coin


class TestCoin:
    def assert_coin(self, expression: str, coin: Coin, expected: Coin):
        assert coin.pp == expected.pp, f"{expression} | PP => {coin} != {expected}"
        assert coin.gp == expected.gp, f"{expression} | GP => {coin} != {expected}"
        assert coin.ep == expected.ep, f"{expression} | EP => {coin} != {expected}"
        assert coin.sp == expected.sp, f"{expression} | SP => {coin} != {expected}"
        assert coin.cp == expected.cp, f"{expression} | CP => {coin} != {expected}"

    @pytest.mark.parametrize(
        "expression, expected_result",
        [
            ("5cp + 5cp", Coin(cp=10)),
            ("2sp + 5cp + 2sp + 5cp", Coin(sp=5)),
            ("5sp + 5sp", Coin(sp=10)),
            ("1ep + 1ep", Coin(ep=2)),
            ("5gp + 5gp", Coin(gp=10)),
            ("1pp + 1pp", Coin(pp=2)),
            ("(1gp + 1ep) + 1ep", Coin(gp=2)),
            ("1ep + (1gp + 1ep)", Coin(gp=2)),
        ],
    )
    def test_addition(self, expression: str, expected_result: Coin):
        result = parse_coin(expression)
        self.assert_coin(expression, result.coin, expected_result)

    @pytest.mark.parametrize(
        "expression, expected_result",
        [
            ("10pp - 5gp", Coin(pp=9, gp=5)),
            ("5gp - 25cp", Coin(gp=4, ep=1, sp=2, cp=5)),
            ("1gp - 5cp", Coin(ep=1, sp=4, cp=5)),
            ("1ep - 5cp", Coin(cp=5, sp=4)),
            ("(2gp + 5sp) - 5sp", Coin(gp=2)),
            ("10gp - (2gp + 5gp)", Coin(gp=3)),
            ("1gp - 11sp", Coin(sp=-1)),
            ("1cp- (1pp + 1gp + 1ep + 1sp + 2cp)", Coin(cp=-1, sp=-1, ep=-1, gp=-1, pp=-1)),
        ],
    )
    def test_subtraction(self, expression: str, expected_result: Coin):
        result = parse_coin(expression)
        self.assert_coin(expression, result.coin, expected_result)

    @pytest.mark.parametrize(
        "expression, expected_result",
        [
            ("5gp * 2", Coin(gp=10)),
            ("15gp * 2", Coin(gp=30)),
            ("2pp * 3", Coin(pp=6)),
            ("5sp * 2", Coin(sp=10)),
            ("5cp * 2", Coin(cp=10)),
            ("10gp * 1.5", Coin(gp=15)),
            ("1pp * 1.5", Coin(pp=1, gp=5)),
            ("2gp * 2.5", Coin(gp=5)),
            ("4sp * 1.5", Coin(sp=6)),
            ("10cp * 1.5", Coin(cp=15)),
            ("(5gp + 5gp) * 1.5", Coin(gp=15)),
        ],
    )
    def test_multiplication(self, expression: str, expected_result: Coin):
        result = parse_coin(expression)
        self.assert_coin(expression, result.coin, expected_result)

    @pytest.mark.parametrize(
        "expression, expected_result",
        [
            ("10gp / 2", Coin(gp=5)),
            ("1pp / 2", Coin(gp=5)),
            ("3pp / 2", Coin(pp=1, gp=5)),
            ("1gp / 2", Coin(ep=1)),
            ("1sp / 2", Coin(cp=5)),
            ("15gp / 1.5", Coin(gp=10)),
            ("1pp / 4", Coin(ep=1, gp=2)),
            ("5gp / 2", Coin(gp=2, ep=1)),
            ("3sp / 1.5", Coin(sp=2)),
            ("15cp / 1.5", Coin(cp=10)),
            ("(10gp + 5gp) / 3", Coin(gp=5)),
        ],
    )
    def test_division(self, expression: str, expected_result: Coin):
        ast = parse_coin(expression)
        self.assert_coin(expression, ast.coin, expected_result)

    @pytest.mark.parametrize(
        "expression",
        [
            ("dungeon master"),
            ("100ip + 100gp"),
            ("1cp *"),
            ("1cp /"),
            ("1cp -"),
            ("1cp +"),
            # Cannot divide coin by coin.
            ("1gp / 1cp"),
            # Cannot multiply coin by coin.
            ("1gp * 1cp"),
        ],
    )
    def test_invalid_syntax(self, expression: str):
        with pytest.raises(ValueError):
            parse_coin(expression)

    @pytest.mark.parametrize(
        "expression, expected_result",
        [
            ("10 + 10", Coin(gp=20)),
            ("5 + 2.5", Coin(gp=7, ep=1)),
            ("10 - 5", Coin(gp=5)),
            ("10 - 2.5", Coin(gp=7, ep=1)),
            ("10 * 2", Coin(gp=20)),
            ("10 * 2.5", Coin(gp=25)),
            ("10 / 5", Coin(gp=2)),
            ("25 / 2.5", Coin(gp=10)),
            ("66", Coin(gp=66)),  # Bug where units would resolve to CP if no expression.
        ],
    )
    def test_default_unit_is_gp(self, expression: str, expected_result: Coin):
        ast = parse_coin(expression)
        self.assert_coin(expression, ast.coin, expected_result)
