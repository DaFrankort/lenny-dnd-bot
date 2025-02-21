import random
import re

class Dice:
    DICE_PATTERN = re.compile(r"^\s*(\d+)d(\d+)([+-]\d+)?\s*$", re.IGNORECASE)

    def __init__(self, dice_notation: str):
        """Parses the dice notation (e.g., '1d20+3') and initializes attributes."""
        match = self.DICE_PATTERN.match(dice_notation)
        self.is_valid = bool(match)

        if not match:
            raise ValueError("Invalid dice format! Use 'NdN' or 'NdN±X' (e.g., 1d20, 2d6+3).")

        self.num_rolls = int(match.group(1))
        self.dice_sides = int(match.group(2))
        self.modifier = int(match.group(3)) if match.group(3) else 0
        self.rolls = []

    def roll(self):
        """Internally rolls the dice, use get_total() to get the result."""
        self.rolls = [random.randint(1, self.dice_sides) for _ in range(self.num_rolls)]

    def get_total(self) -> int:
        """Returns the total of the rolled dice + modifier"""
        if self.rolls is None:
            raise RuntimeError("No roll has been made yet! Call roll() before getting the total.")
        
        return sum(self.rolls) + self.modifier

    def __str__(self):
        """Returns a formatted string representation of the roll result."""
        if self.rolls is None:
            raise RuntimeError("No roll has been made yet! Call roll() first before attempting to print the dice as string.")

        total_text = f"**{self.get_total()}**"
        rolls_text = f"({', '.join(map(str, self.rolls))})"
        modifier_text = f"{'+' if self.modifier > 0 else '-' if self.modifier < 0 else ''} {abs(self.modifier)}" if self.modifier else ""
        
        if len(self.rolls) != 1 or self.modifier:
            return f"{rolls_text} {modifier_text} => {total_text}"

        return total_text
        

