import math
import re


class Coin:
    pp: float
    gp: float
    ep: float
    sp: float
    cp: float

    def __init__(self, cp: float = 0, sp: float = 0, ep: float = 0, gp: float = 0, pp: float = 0):
        self.pp, self.gp, self.ep, self.sp, self.cp = pp, gp, ep, sp, cp
        self.break_down()

    @property
    def total_cp(self) -> float:
        """Converts the entire wallet into a single Copper value."""
        return (self.pp * 1000) + (self.gp * 100) + (self.ep * 50) + (self.sp * 10) + self.cp

    @classmethod
    def from_string(cls, expression: str) -> "Coin":
        parts = re.split(r"([+\-*/])", expression)
        expression = expression.lower().strip().replace(" ", "")
        total = Coin()
        op = "+"

        for part in parts:
            part = part.strip().lower()
            if not part:
                continue

            if part in ("+", "-", "*", "/"):
                op = part
                continue

            if op == "+":
                total += cls._parse_block(part)
            elif op == "-":
                total -= cls._parse_block(part)
            elif op == "*":
                total *= float(part)
            elif op == "/":
                total /= float(part)
        return total

    @classmethod
    def _parse_block(cls, block: str) -> "Coin":
        data = {"pp": 0.0, "gp": 0.0, "ep": 0.0, "sp": 0.0, "cp": 0.0}
        matches = re.findall(r"([\d.]+)\s*([a-z]+)", block)
        for value, label in matches:
            if label in data:
                data[label] += float(value)

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

    def break_down(self):
        """
        Only converts larger coins to smaller ones if
        a denomination is negative.
        """
        if self.cp < 0:
            needed_sp = math.ceil(abs(self.cp) / 10)
            self.sp -= needed_sp
            self.cp += needed_sp * 10

        if self.sp < 0:
            needed_ep = math.ceil(abs(self.sp) / 5)
            self.ep -= needed_ep
            self.sp += needed_ep * 5

        if self.ep < 0:
            needed_gp = math.ceil(abs(self.ep) / 2)
            self.gp -= needed_gp
            self.ep += needed_gp * 2

        if self.gp < 0:
            needed_pp = math.ceil(abs(self.gp) / 10)
            self.pp -= needed_pp
            self.gp += needed_pp * 10

    def __add__(self, other: "Coin") -> "Coin":
        return Coin(
            cp=self.cp + other.cp, sp=self.sp + other.sp, ep=self.ep + other.ep, gp=self.gp + other.gp, pp=self.pp + other.pp
        )

    def __sub__(self, other: "Coin") -> "Coin":
        return Coin(
            cp=self.cp - other.cp, sp=self.sp - other.sp, ep=self.ep - other.ep, gp=self.gp - other.gp, pp=self.pp - other.pp
        )

    def __mul__(self, other: float) -> "Coin":
        return Coin(cp=self.cp * other, sp=self.sp * other, ep=self.ep * other, gp=self.gp * other, pp=self.pp * other)

    def __truediv__(self, other: float) -> "Coin":
        return Coin(cp=self.cp / other, sp=self.sp / other, ep=self.ep / other, gp=self.gp / other, pp=self.pp / other)

    def __str__(self) -> str:
        def format(val: float):
            val = round(val, 2)
            return int(val) if val == int(val) else val

        denominations = [
            (self.pp, "PP"),
            (self.gp, "GP"),
            (self.ep, "EP"),
            (self.sp, "SP"),
            (self.cp, "CP"),
        ]

        result = [f"{format(val)} {label}" for val, label in denominations if val]
        return ", ".join(result) if result else "0 CP"
