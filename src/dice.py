import logging
import random
import re
import discord
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
    is_positive: bool
    is_valid: bool

    roll_amount: int
    sides: int
    rolls: list[int]
    warnings: list[str]
    
    def __init__(self, die_notation: str, is_positive: bool = True):
        match = _Die.match(die_notation)
        self.is_valid = True
        self.is_positive = is_positive
        self.rolls = []
        self.warnings = []

        if not match:
            logging.error(f"Invalid die notation: \'{die_notation}\', should be in the format NdN (e.g., 2d6, 1d20).")
            self.is_valid = False
            return

        roll_amount = int(match.group(1))
        sides = int(match.group(2))
        if sides == 0:
            sides = 1

        roll_amount_limit = 128
        if roll_amount > roll_amount_limit:
            self.warnings.append(f"Roll amount in \'{die_notation}\' exceeds limit, altered from **{roll_amount}** to **{roll_amount_limit}**")
            roll_amount = roll_amount_limit
        self.roll_amount = roll_amount

        sides_limit = 2048
        if sides > sides_limit:
            self.warnings.append(f"Side amount in \'{die_notation}\' exceeds limit, altered from **{sides}** to **{sides_limit}**")
            sides = sides_limit
        self.sides = sides

    def roll(self):
        """Generates random values for each die-roll, stores the results in the rolls list."""
        self.rolls = [random.randint(1, self.sides) for _ in range(self.roll_amount)]
        logging.debug(f"Rolled {self.roll_amount}d{self.sides} with result: {self.__str__}")
    
    def get_total(self) -> int:
        """Calculates and returns the total of all dice rolls, considering the sign of the die."""

        if self.rolls == None:
            raise RuntimeError("No roll has been made yet! Call roll() before getting the total.") # TODO will be refactored => Dice rolls will be automatically rolled when creating a DiceExpression
        
        roll_sum = sum(self.rolls)
        if self.is_positive:
            return roll_sum
        return -roll_sum
    
    def __str__(self):
        operator = '+' if self.is_positive else '-'
        roll_list = ', '.join(map(str, self.rolls)) # Convert rolls to list of strings with comma separation
        return f"{operator}({roll_list})"
    
    @staticmethod
    def match(die_notation: str) -> (re.Match[str] | None):
        """Matches a dice notation string to the format 'NdN' (e.g., '2d6', '1d20')."""
        return re.fullmatch(r'(\d+)d(\d+)', die_notation.lower())
    
    def is_single_roll(self) -> bool:
        return self.roll_amount == 1
    
    def is_natural_twenty(self) -> bool:
        if not self.is_single_roll():
            return False
        return self.sides == 20 and self.rolls[0] == 20
    
    def is_natural_one(self) -> bool:
        if not self.is_single_roll():
            return False
        return self.sides == 20 and self.rolls[0] == 1

class _Modifier:
    """Private class used to represent a modifier in a dice expression."""
    is_positive: bool
    is_valid: bool

    value: int
    warnings: list[str]

    def __init__(self, value: str, is_positive: bool = True):
        self.is_valid = True
        self.is_positive = is_positive
        self.warnings = []

        if not value.isdigit():
            logging.error(f"Invalid modifier notation: \'{value}\', should be a number.")
            self.is_valid = False
            return
        
        value = int(value)
        value_limit = 8192
        if value > value_limit:
            self.warnings.append(f"Modifier \'{value}\' exceeds limit, altered to **{value_limit}**")
            value = value_limit
        self.value = value

    def __str__(self):
        operator = '+' if self.is_positive else '-'
        return f"{operator}{self.value}"
    
    def get_value(self) -> int:
        """Returns the value of the modifier, considering its sign."""
        if self.is_positive:
            return self.value
        return -self.value

class DiceExpression:
    """Represents a dice expression (e.g., '2d6+1') and provides functionality to parse, validate, roll, and calculate the total value of the expression."""
    notation: str
    _is_valid: bool

    dice: list[_Die]
    modifiers: list[_Modifier]
    steps: list[_Die | _Modifier] # In some cases we need to keep track of the order of operations, so we keep a general list of steps.

    def __init__(self, die_notation: str):
        die_notation = self._sanitize_die_notation(die_notation)
        self.notation = die_notation
        self._is_valid = True
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
        steps = []

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
                logging.error(f"Invalid part in dice notation: {part}")
                print(f"Invalid part in dice notation: {part}")
                self._is_valid = False
                break
            
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

    def has_only_one_die(self) -> bool:
        """Checks if the expression contains only one die."""
        return len(self.dice) == 1

    def roll(self):
        for die in self.dice:
            if isinstance(die, _Die):
                die.roll()
    
    def get_total(self) -> int:
        """Calculates and returns the total value of the dice expression."""
        total = 0

        for die in self.dice:
            total += die.get_total()

        for mod in self.modifiers:
            total += mod.get_value()

        return total

    def __str__(self):
        """Generates and returns a formatted string representation of the dice roll result."""
        total_text = f"**{self.get_total()}**"
        if self.has_only_one_die() and self.dice[0].is_single_roll() and len(self.modifiers) == 0: # Only show total if there's only 1 1-roll die without modifiers.
            return total_text
        
        steps_text = ''.join(str(step) for step in self.steps)
        if steps_text.startswith('+'):
            steps_text = steps_text[1:] # Remove leading '+'

        return f"``{steps_text}`` -> {total_text}"
    
    def is_dirty_twenty(self) -> bool:
        if len(self.dice) != 1:
            return False # Only applies to single dice rolls (e.g., 1d20 / 1d20+1)
        
        if self.dice[0].sides != 20 or self.dice[0].roll_amount != 1:
            return False # Only applies to 1d20 rolls
        
        return self.get_total() == 20
    
    def get_warnings(self) -> list[str]:
        warnings = []

        for die in self.dice:
            if len(die.warnings) > 0:
                warnings.extend(die.warnings)

        for mod in self.modifiers:
            if len(mod.warnings) > 0:
                warnings.extend(mod.warnings)

        return list(dict.fromkeys(warnings)) # Remove duplicates by turning into a dict and back to a list
    
    def get_warnings_text(self) -> str:
        return '\n'.join(f'⚠️ {w}' for w in self.get_warnings())
    
    def has_warnings(self) -> bool:
        return len(self.get_warnings()) != 0
    
    def is_valid(self) -> bool:
        for die in self.dice:
            if not die.is_valid:
                return False
            
        for mod in self.modifiers:
            if not mod.is_valid:
                return False
        
        return self._is_valid

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
    expressions: list[DiceExpression]
    reason: str
    mode: RollMode
    
    def __init__(self, ctx: discord.Interaction, expressions: list[DiceExpression], reason: str | None = None,  mode: RollMode = RollMode.NORMAL):
        self.username = ctx.user.display_name
        self.avatar_url = ctx.user.avatar.url
        self.user_id = str(ctx.user.id)
        self.expressions = expressions
        self.reason = reason if reason != None else "Result"
        self.mode = mode
        self.color = UserColor.get(ctx)

    def _should_only_show_results(self) -> bool:
        """Returns True if the embed should only display the roll result (e.g., a single clean 1d20)."""
        if len(self.expressions) != 1:
            return False # Don't show for cases like advantage/disadvantage
        if len(self.expressions[0].steps) != 1:
            return False
        if len(self.expressions[0].dice) != 1:
            return False
        if not self.expressions[0].dice[0].is_single_roll():
            return False

        return True

    def _get_title(self) -> str:
        """Generates a title string based on the current roll mode and dice notation."""

        match self.mode:
            case RollMode.NORMAL:
                return f"Rolled {self.expressions[0].notation}!"
            
            case RollMode.ADVANTAGE:
                return f"Rolled {self.expressions[0].notation} with advantage!"
            
            case RollMode.DISADVANTAGE:
                return f"Rolled {self.expressions[0].notation} with disadvantage!"

    def _get_description(self) -> str:
        description = ""
        extra_message = ""

        # Always build the description if multiple dice, or more than 1 DiceExpression
        if not self._should_only_show_results():
            for expression in self.expressions:
                description += f"- {expression}\n"

        # Always evaluate dice for critical outcomes
        for expression in self.expressions:
            if not expression.has_only_one_die():
                continue # Only applies to single dice rolls (e.g., 1d20 / 1d20+1)
            if not expression.dice[0].is_single_roll():
                continue # Only applies to single rolls
            if expression.dice[0].sides != 20:
                continue # Only applies to 1d20 rolls

            if expression.dice[0].is_natural_twenty():
                extra_message = "🎯 **Critical Hit!**"
            elif expression.dice[0].is_natural_one():
                extra_message = "💀 **Critical Fail!**"
            elif expression.is_dirty_twenty():
                extra_message = "⚔️ **Dirty 20!**"

        match self.mode:
            case RollMode.NORMAL:
                total = f"**{self.expressions[0].get_total()}**"
                return description + f"🎲 **{self.reason}:** {total}" + (f"\n{extra_message}" if extra_message else "")
            
            case RollMode.ADVANTAGE:
                largest_value = max(self.expressions[0].get_total(), self.expressions[1].get_total())
                return description + f"🎲 **{self.reason}: {largest_value}**"
            
            case RollMode.DISADVANTAGE:
                smallest_value = min(self.expressions[0].get_total(), self.expressions[1].get_total())
                return description + f"🎲 **{self.reason}: {smallest_value}**"

    def build(self) -> discord.Embed:
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