import logging
import random
import re
import discord
import sys
from enum import Enum
from user_colors import UserColor

class _Die:
    """
    Private class used to represent and manipulate dice rolls in the NdN format.

    This class encapsulates the logic for parsing, validating, and rolling dice
    based on the NdN notation (e.g., '2d6', '1d20'). It provides methods to roll
    the dice, calculate the total of the rolls, and represent the results as a string.
    Instances of this class are typically used as part of a DiceExpression object's steps
    to handle individual dice rolls.
    """
    is_valid: bool
    is_positive: bool

    roll_amount: int
    sides: int
    rolls: list[int]
    
    def __init__(self, die_notation: str, is_positive: bool = True):
        match = _Die.match(die_notation)
        self.is_valid = True
        self.is_positive = is_positive

        if not match:
            self.is_valid = False
            logging.error("Invalid die notation. Use the format 'NdN' (e.g., '2d20').")
            return

        roll_amount = int(match.group(1))
        sides = int(match.group(2))
        if sides == 0:
            sides = 1

        self.roll_amount = min(roll_amount, 128)
        self.sides = min(sides, 256)
        self.rolls = []

    def roll(self):
        """Generates random values for each die-roll, stores the results in the rolls list."""
        self.rolls = [random.randint(1, self.sides) for _ in range(self.roll_amount)]
        logging.debug(f"Rolled {self.roll_amount}d{self.sides} with result: {self.__str__}")
    
    def get_total(self) -> int:
        """
        Calculates and returns the total of all dice rolls.
        Returns:
            int: The total of all dice rolls, capped at `sys.maxsize`.
        Raises:
            RuntimeError: If no rolls have been made (i.e., `rolls` is None).
        """

        if self.rolls == None:
            raise RuntimeError("No roll has been made yet! Call roll() before getting the total.")
        return min(sum(self.rolls), sys.maxsize)
    
    def __str__(self):
        operator = '+' if self.is_positive else '-'
        return f"{operator} ({', '.join(map(str, self.rolls))})"
    
    @staticmethod
    def match(die_notation: str) -> (re.Match[str] | None):
        """Matches a dice notation string to the format 'NdN' (e.g., '2d6', '1d20')."""
        return re.fullmatch(r'(\d+)d(\d+)', die_notation.lower())

class _Modifier:
    """Private class used to represent a modifier in a dice expression."""
    value: int
    is_positive: bool

    def __init__(self, value: str, is_positive: bool = True):
        self.is_positive = is_positive

        if not value.isdigit():
            logging.error("Invalid modifier notation. Use a number (e.g., '1', '2').")
            return
        
        value = min(int(value), 8192) # Limit to 8192 to prevent overflow
        self.value = value

    def __str__(self):
        operator = '+' if self.is_positive else '-'
        return f"{operator} {self.value}"

class DiceExpression:
    """Represents a dice expression (e.g., '2d6+1') and provides functionality to parse, validate, roll, and calculate the total value of the expression."""
    notation: str
    is_valid: bool # TODO Rework

    dice: list[_Die]
    modifiers: list[_Modifier]
    steps: list[_Die | _Modifier]

    def __init__(self, die_notation: str):
        die_notation = self._sanitize_die_notation(die_notation)
        self.notation = die_notation
        self.is_valid = True
        self.dice, self.modifiers, self.steps = self._notation_to_steps(die_notation)

        self.roll()

    def _notation_to_steps(self, notation: str) -> tuple[list[_Die], list[_Modifier], list[_Die | _Modifier]]:
        """
        Converts a dice notation string into a list of dice, modifiers, and steps.
        Returns:
            tuple: A tuple containing three lists:
            - dice (list[_Die]): List of _Die objects parsed from the notation.
            - modifiers (list[_Modifier]): List of _Modifier objects parsed from the notation.
            - steps (list[_Die | _Modifier]): Ordered list of steps (dice and modifiers) for the expression.
        """
        dice = []
        modifiers = []
        steps = [] # In some cases we need to keep track of the order of operations, so we keep a general list of steps.

        # Split notation into parts, (e.g., '2d6', '+1', '-2d4')
        parts = re.split(r'([+-]?\d+d\d+|[+-]?\d+)', notation)

        for part in parts:
            part = part.strip()
            if not part:
                continue # Skip empty parts

            is_positive = not part.startswith('-')
            part = part.lstrip('+-')

            if _Die.match(part):
                die = _Die(part, is_positive)
                dice.append(die)
                steps.append(die)

            elif part.isdigit():
                mod = _Modifier(part, is_positive)
                modifiers.append(mod)
                steps.append(mod)

            else:
                raise ValueError(f"Invalid part in dice notation: {part}")
            
        return dice, modifiers, steps

    def _sanitize_die_notation(self, notation: str) -> str:
        """Sanitizes the dice notation by removing spaces and irrelevant characters."""
        notation = notation.lower().replace(" ", "") # force to lowercas & remove spaces
        notation = re.sub(r"[^0-9d+\-]", "", notation) # remove irrelevant character (anything not 1d20+1 related)

        # Collapse repeated characters into 1
        notation = re.sub(r"\++", "+", notation)
        notation = re.sub(r"\-+", "-", notation)
        notation = re.sub(r"d+", "d", notation)

        notation = re.sub(r'(?<!\d)d', '1d', notation)  # add 1 before standalone 'd' (Convert d20 => 1d20)
        return notation

    def is_only_one_die(self) -> bool:
        """Checks if the expression contains only one die with one roll."""
        if len(self.steps) != 1:
            return False # More than 1 step, so not a single die.
        return len(self.dice) == 1 and self.dice[0].roll_amount == 1 # Single die with 1 roll.

    def roll(self):
        for die in self.dice:
            if isinstance(die, _Die):
                die.roll()
    
    def get_total(self) -> int:
        """Calculates and returns the total value of the dice expression."""
        total = 0

        def is_over_value_threshold(value: int) -> int:
            """Checks if the value exceeds a certain threshold."""
            return value > sys.maxsize / 2

        # Dice
        for die in self.dice:
            if is_over_value_threshold(total):
                break

            if die.is_positive:
                total += die.get_total()
            else:
                total -= die.get_total()
        
        # Modifiers
        for mod in self.modifiers:
            if is_over_value_threshold(total):
                break

            if mod.is_positive:
                total += mod.value
            else:
                total -= mod.value

        return total

    def __str__(self):
        """Generates and returns a formatted string representation of the dice roll result."""
        total_text = f"**{self.get_total()}**"
        if self.is_only_one_die(): # Only show total if there's only 1 step.
            return total_text
        
        steps_text = ' '.join(str(step) for step in self.steps)
        if steps_text.startswith('+ '):
            steps_text = steps_text[2:] # Remove leading '+ '

        return f"``{steps_text}`` -> {total_text}"

class RollMode(Enum):
    """An enumeration representing the different modes of rolling dice in a Dungeons & Dragons context."""
    NORMAL = "normal"
    ADVANTAGE = "advantage"
    DISADVANTAGE = "disadvantage"

class DiceEmbed:
    """A class to create and manage Discord embed messages for dice roll results."""
    username: str
    avatar_url: str
    user_id: str
    dice: list[DiceExpression]
    reason: str
    mode: RollMode
    
    def __init__(self, ctx: discord.Interaction, dice: list[DiceExpression], reason: str | None = None,  mode: RollMode = RollMode.NORMAL):
        self.username = ctx.user.display_name
        self.avatar_url = ctx.user.avatar.url
        self.user_id = str(ctx.user.id)
        self.dice = dice
        self.reason = reason if reason != None else "Result"
        self.mode = mode
        self.color = UserColor.get(ctx)

    def _get_title(self) -> str:
        """Generates a title string based on the current roll mode and dice notation."""

        match self.mode:
            case RollMode.NORMAL:
                return f"Rolled {self.dice[0].notation}!"
            
            case RollMode.ADVANTAGE:
                return f"Rolled {self.dice[0].notation} with advantage!"
            
            case RollMode.DISADVANTAGE:
                return f"Rolled {self.dice[0].notation} with disadvantage!"

    def _get_description(self) -> str:
        """
        Generates a description of the dice roll results, including critical outcomes and roll mode.
        This method constructs a detailed description of the dice rolls, evaluates for critical outcomes 
        (e.g., critical hit, critical fail, or dirty 20), and formats the result based on the roll mode 
        (NORMAL, ADVANTAGE, or DISADVANTAGE).
        """

        description = ""
        extra_message = ""

        # Always build the description if multiple dice, or more than 1 roll
        if not (self.dice[0].is_only_one_die() and len(self.dice) == 1):
            for die in self.dice:
                description += f"- {die}\n"

        # Always evaluate dice for critical outcomes
        for die in self.dice:
            if (
                len(die.steps) == 2
                and isinstance(die.steps[1], _Die)
                and die.steps[1].roll_amount == 1
                and die.steps[1].sides == 20
            ):
                rolled_value = die.steps[1].rolls[0]
                total = die.get_total()

                if rolled_value == 20:
                    extra_message = "🎯 **Critical Hit!**"
                elif rolled_value == 1:
                    extra_message = "💀 **Critical Fail!**"
                elif total == 20:
                    extra_message = "⚔️ **Dirty 20!**"

        match self.mode:
            case RollMode.NORMAL:
                dice_text = self.dice[0] if self.dice[0].is_only_one_die() else f"**{self.dice[0].get_total()}**"
                return description + f"🎲 **{self.reason}:** {dice_text}\n" + (f"\n{extra_message}" if extra_message else "")
            
            case RollMode.ADVANTAGE:
                largest_value = max(self.dice[0].get_total(), self.dice[1].get_total())
                return description + f"🎲 **{self.reason}: {largest_value}**"
            
            case RollMode.DISADVANTAGE:
                smallest_value = min(self.dice[0].get_total(), self.dice[1].get_total())
                return description + f"🎲 **{self.reason}: {smallest_value}**"

    def build(self) -> discord.Embed:
        """
        Builds and returns a Discord embed object with the specified attributes.
        The embed object is configured with a description, author details, and color.
        """

        embed = discord.Embed(
            type="rich",
            description=self._get_description()
        )
        embed.set_author(
            name=self._get_title(),
            icon_url=self.avatar_url
        )
        embed.color = self.color
        return embed