import random
import re

class Dice:
    def __init__(self, dice_notation: str):
        """Parses the dice notation (e.g., '1d20+3') and initializes attributes."""
        match = re.fullmatch(r"(\d+)d(\d+)([+-]\d+)?", dice_notation.lower())

        if not match:
            raise ValueError("Invalid dice format! Use 'NdN' or 'NdN±X' (e.g., 1d20, 2d6+3).")

        self.num_rolls = int(match.group(1))   # Number of dice
        self.dice_sides = int(match.group(2))  # Dice type (e.g., d20)
        self.modifier = int(match.group(3)) if match.group(3) else 0  # Modifier (optional)
        self.rolls = []  # Stores individual roll results

    def roll(self):
        """Rolls the dice and applies the modifier."""
        self.rolls = [random.randint(1, self.dice_sides) for _ in range(self.num_rolls)]
        total = sum(self.rolls) + self.modifier
        return total

    def __str__(self):
        """Returns a formatted string representation of the roll result."""
        modifier_text = f" {self.modifier:+}" if self.modifier else ""  # Shows +X or -X
        return f"🎲 Rolls: {', '.join(map(str, self.rolls))}{modifier_text} = **{self.roll()}**"

