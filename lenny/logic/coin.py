import re


class CoinNode:

    def eval(self) -> "Coin | float":
        raise NotImplementedError()


class ValueNode(CoinNode):

    def __init__(self, value: "Coin | float"):
        self.value = value

    def eval(self) -> "Coin | float":
        return self.value


class BinOpNode(CoinNode):
    def __init__(self, left: ValueNode, op: str, right: ValueNode):
        self.left, self.op, self.right = left, op, right

    def eval(self) -> "Coin | float":
        left_val = self.left.eval()
        right_val = self.right.eval()

        if self.op == "+":
            return left_val + right_val  # type: ignore
        if self.op == "-":
            return left_val - right_val  # type: ignore
        if self.op == "*":
            return left_val * right_val  # type: ignore
        if self.op == "/":
            return left_val / right_val  # type: ignore
        raise ValueError(f"Unknown operator: {self.op}")


class CoinParser:
    def __init__(self, tokens: list[str]):
        self.tokens = tokens
        self.pos = 0

    def consume(self):
        res = self.tokens[self.pos] if self.pos < len(self.tokens) else None
        self.pos += 1
        return res

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def parse(self) -> CoinNode:
        return self.expr()

    def expr(self) -> CoinNode:
        node = self.term()
        while self.peek() in {"+", "-"}:
            op = self.consume()
            if op:
                node = BinOpNode(node, op, self.term())  # type: ignore
        return node

    def term(self) -> CoinNode:
        node = self.factor()
        while self.peek() in {"*", "/"}:
            op = self.consume()
            if op:
                node = BinOpNode(node, op, self.factor())  # type: ignore
        return node

    def factor(self) -> CoinNode:
        token = self.consume()
        if not token:
            raise ValueError("Unexpected end of expression")

        if token == "(":
            node = self.expr()
            self.consume()  # consume ')'
            return node

        if re.search(r"[a-z]", token):
            coin = Coin.parse_unit(token)
            while True:
                # Users can do "wallet"-notations like so: 100gp 20sp + x
                # In cases where there isn't an operator between pieces, we sum them up and treat them as one collection of pieces, or a "wallet".
                next_token = self.peek()
                if not next_token or not re.search(r"[a-z]", next_token):
                    break

                coin += Coin.parse_unit(self.consume())  # type: ignore

            return ValueNode(coin)

        return ValueNode(float(token))


class Coin:
    pp: float
    gp: float
    ep: float
    sp: float
    cp: float

    def __init__(self, cp: float = 0, sp: float = 0, ep: float = 0, gp: float = 0, pp: float = 0):
        self.pp, self.gp, self.ep, self.sp, self.cp = pp, gp, ep, sp, cp
        self.round_up()

    @property
    def total_cp(self) -> float:
        """Converts the entire wallet into a single Copper value."""
        return (self.pp * 1000) + (self.gp * 100) + (self.ep * 50) + (self.sp * 10) + self.cp

    @classmethod
    def from_string(cls, expression: str) -> "Coin":
        tokens = cls._tokenize(expression)
        parser = CoinParser(tokens)
        result = parser.parse().eval()
        if isinstance(result, (float, int)):
            return Coin(cp=result)
        return result

    @staticmethod
    def _tokenize(expression: str):
        token_pattern = re.compile(r"(\d*\.\d+|\d+)[a-z]+|(\d*\.\d+|\d+)|[+\-*/()]")
        return [m.group(0) for m in token_pattern.finditer(expression.lower().replace(" ", ""))]

    @classmethod
    def parse_unit(cls, block: str) -> "Coin":
        data = {"pp": 0.0, "gp": 0.0, "ep": 0.0, "sp": 0.0, "cp": 0.0}
        match = re.match(r"([\d.]+)([a-z]+)", block)
        if match:
            val, unit = match.groups()
            data[unit] = float(val)
        return cls(**data)

    def round_up(self):
        """
        Converts all coins to the perfect amount, as if perfectly exchanged at a bank.
        """

        total = self.total_cp
        self.pp, remainder = divmod(total, 1000)
        self.gp, remainder = divmod(remainder, 100)
        self.ep, remainder = divmod(remainder, 50)
        self.sp, self.cp = divmod(remainder, 10)

    def __add__(self, other: "Coin") -> "Coin":
        return Coin(cp=self.total_cp + other.total_cp)

    def __sub__(self, other: "Coin") -> "Coin":
        return Coin(cp=self.total_cp - other.total_cp)

    def __mul__(self, other: float) -> "Coin":
        return Coin(cp=self.total_cp * other)

    def __truediv__(self, other: float) -> "Coin":
        return Coin(cp=self.total_cp / other)

    def __str__(self) -> str:

        def format_val(val: float):
            val = round(val, 2)
            return int(val) if val == int(val) else val

        denominations = [
            (self.cp, "CP"),
            (self.sp, "SP"),
            (self.ep, "EP"),
            (self.gp, "GP"),
            (self.pp, "PP"),
        ]

        result = [f"``{format_val(val)}`` {label}" for val, label in denominations if val]
        return ", ".join(result) if result else "0 CP"

    def __repr__(self) -> str:
        parts: list[str] = []

        for name in ("cp", "sp", "ep", "gp", "pp"):
            value = getattr(self, name)
            if value:
                parts.append(f"{name}={value}")

        parts.append(f"total_cp={self.total_cp}")

        return f"Coin({', '.join(parts)})"
