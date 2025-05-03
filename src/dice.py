import logging
import random
import re
import discord
import sys
from enum import Enum
from user_colors import UserColor

def _match_NdN(die_notation: str) -> (re.Match[str] | None):
    """Matches a dice notation string of the format 'NdN' (e.g., '2d6', '1d20')."""
    return re.fullmatch(r'(\d+)d(\d+)', die_notation.lower())

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
    roll_amount: int
    sides: int
    rolls: list[int]
    
    def __init__(self, die_notation: str):
        match = _match_NdN(die_notation)
        self.is_valid = True

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
        return f"({', '.join(map(str, self.rolls))})"

class DiceExpression:
    """Represents a dice expression (e.g., '2d6+1') and provides functionality to parse, validate, roll, and calculate the total value of the expression."""
    notation: str
    is_valid: bool
    steps: list[str | int | _Die]

    def __init__(self, die_notation: str):
        die_notation = self._sanitize_die_notation(die_notation)
        self.notation = die_notation
        self.is_valid = True

        if die_notation[0] in "+-": # Add leading operators
            self.steps = [die_notation[0]]
            die_notation = die_notation[1:]
        else:
            self.steps = ['+']

        parts = re.split(r'([+-])', die_notation)

        for part in parts:
            if len(self.steps) > 32:
                self.is_valid = False
                logging.error(f"User's dice expression has too many steps.")
                break

            if part == "+" or part == "-":
                self.steps.append(part) # + or -
            elif _match_NdN(part):
                self.steps.append(_Die(part)) # Die (NdN)
            elif part.isdigit():
                self.steps.append(min(int(part), 8192)) # Modifier, limited to 10% of maxint
            else:
                self.is_valid = False
                logging.error(f"Invalid token in dice expression: {part}.")
                return
        
        self.roll()

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
        if len(self.steps) != 2:
            return False

        return len(self.steps) == 2 and isinstance(self.steps[1], _Die) and self.steps[1].roll_amount == 1

    def roll(self):
        for step in self.steps:
            if isinstance(step, _Die):
                step.roll()
    
    def get_total(self) -> int:
        total = 0
        for i in range(0, len(self.steps), 2):
            operator = self.steps[i]
            value = self.steps[i+1]

            if isinstance(value, _Die):
                value = value.get_total()

            if operator == '+':
                total += value
            elif operator == '-':
                total -= value

            if total > sys.maxsize / 2:
                logging.warning("DiceExpression total too large whilst calculating total, stopped calculation to prevent errors.")
                break
        return total

    def __str__(self):
        """Generates and returns a formatted string representation of the dice roll result."""
        total_text = f"**{self.get_total()}**"
        steps_text = ' '.join(str(step) for step in self.steps[1:])
        
        if self.steps[0] == '-':
            steps_text = f"- {steps_text}"

        if len(self.steps) == 2 and isinstance(self.steps[1], _Die): # Only show total if there's only 1 step.
            if len(self.steps[1].rolls) == 1:
                return total_text

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