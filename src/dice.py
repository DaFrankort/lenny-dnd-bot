import logging
import random
import re
import discord
import sys
from discord.ext import commands
from enum import Enum
from user_colors import UserColor

def _match_NdN(die_notation: str):
    return re.fullmatch(r'(\d+)d(\d+)', die_notation.lower())

class _Die:
    is_valid: bool
    rolls: int
    sides: int
    rolls: list[int]

    """PRIVATE class used to store NdN values and easily manipulate them within a Dice's steps."""
    def __init__(self, die_notation: str):
        match = _match_NdN(die_notation)
        self.is_valid = True

        if not match:
            self.is_valid = False
            print(" !!! Invalid die notation. Use the format 'NdN' (e.g., '2d20'). !!! ")
            return

        roll_amount = int(match.group(1))
        sides = int(match.group(2))
        if sides == 0:
            sides = 1

        self.roll_amount = min(roll_amount, 128)
        self.sides = min(sides, 256)
        self.rolls = []

    def roll(self):
        """Randomise rolled values"""
        self.rolls = [random.randint(1, self.sides) for _ in range(self.roll_amount)]
    
    def get_total(self):
        if self.rolls == None:
            raise RuntimeError("No roll has been made yet! Call roll() before getting the total.")
        return min(sum(self.rolls), sys.maxsize)
    
    def __str__(self):
        return f"({', '.join(map(str, self.rolls))})"

class Dice:
    """Used to convert a die_notation (ex. 2d6+1) to a randomized value."""
    notation: str
    is_valid: bool
    steps: list[str | int | _Die]

    def __init__(self, die_notation: str):
        self.notation = die_notation.lower()
        self.is_valid = True

        if die_notation[0] in "+-":
            self.steps = [die_notation[0]]
            die_notation = die_notation[1:]
        else:
            self.steps = ['+']

        parts = re.split(r'([+-])', die_notation)

        for part in parts:
            if len(self.steps) > 32:
                self.is_valid = False
                print(f" !!! User's expression has too many steps !!!")
                break

            if part == "+" or part == "-":
                self.steps.append(part) # + or -
            elif _match_NdN(part):
                self.steps.append(_Die(part)) # Die (NdN)
            elif part.isdigit():
                self.steps.append(min(int(part), 8192)) # Modifier, limited to 10% of maxint
            else:
                self.is_valid = False
                print(f" !!! Invalid token in dice expression: {part} !!!")
                return
        
        self.roll()

    def roll(self):
        """Randomise all NdN values within the Dice"""
        for step in self.steps:
            if isinstance(step, _Die):
                step.roll()
    
    def get_total(self) -> int:
        """Returns the total of the rolled dice"""
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
                print(" !!! Total exceeding threshold value! !!!")
                break
        return total

    def __str__(self):
        """Returns a formatted string representation of the roll result."""
        total_text = f"**{self.get_total()}**"
        steps_text = ' '.join(str(step) for step in self.steps[1:])
        
        if self.steps[0] == '-':
            steps_text = f"- {steps_text}"

        if len(self.steps) == 2 & isinstance(self.steps[1], _Die): # Only show total if there's only 1 step.
            if len(self.steps[1].rolls) == 1:
                return total_text

        return f"{steps_text} => {total_text}"

class RollMode(Enum):
    NORMAL = "normal"
    ADVANTAGE = "advantage"
    DISADVANTAGE = "disadvantage"

class DiceEmbed:
    username: str
    avatar_url: str
    user_id: str
    dice: list[Dice]
    reason: str
    mode: RollMode
    
    def __init__(self, ctx: commands.Context, dice: list[Dice], reason: str | None,  mode: RollMode = RollMode.NORMAL):
        self.username = ctx.user.display_name
        self.avatar_url = ctx.user.avatar.url
        self.user_id = str(ctx.user.id)
        self.dice = dice
        self.reason = reason if reason is not None else reason
        self.mode = mode
        return
    
    def __generate_user_color(self):
        """Coding master Tomlolo's AMAZING code to get a hex value from a username.\n
        Turns the first 6 letters of a user's username into a hex-value for color.\n
        """
        hex_value = ""
        hex_place = 0

        # This cute little function converts characters into unicode
        # I made it so the the alpha_value assignment line wouldn't be so hard to read
        def get_alpha(char):
            return abs(ord(char.lower())-96)

        while hex_place < 6:
            try:
                alpha_value = get_alpha(self.username[hex_place]) * get_alpha(self.username[hex_place + 1])
            except:
                # When username is shorter than 6 characters, inserts replacement value.
                alpha_value = 0 # Value can be changed to 255 for light and blue colors, 0 for dark and red colors.

            if alpha_value > 255:
                alpha_value = alpha_value & 255
                
            if alpha_value < 16:
                hex_value = hex_value + "0" + hex(alpha_value)[2:]
            else:
                hex_value = hex_value + hex(alpha_value)[2:]

            hex_place += 2
        return hex_value

    def _get_embed_color(self):
        """
        Gets a user's self-defined color, if no color is set generates a color using the username as seed. \n
        Returns a discord.Color value
        """
        hex_value = UserColor.load(self.user_id)
        if hex_value == None:
            hex_value = self.__generate_user_color()
        
        return discord.Color.from_str("#" + hex_value)
    
    def _get_title(self):
        match self.mode:
            case RollMode.NORMAL:
                return f"Rolled {self.dice[0].notation}!"
            
            case RollMode.ADVANTAGE:
                return f"Rolled {self.dice[0].notation} with advantage!"
            
            case RollMode.DISADVANTAGE:
                return f"Rolled {self.dice[0].notation} with disadvantage!"

    def _get_description(self):
        prefix = "Result" if self.reason == None else self.reason

        match self.mode:
            case RollMode.NORMAL:
                return f"🎲 **{prefix}:** {self.dice[0]}\n"
            
            case RollMode.ADVANTAGE:
                largest_value = max(self.dice[0].get_total(), self.dice[1].get_total())
                return (
                    f"🎲 **{prefix}:** {largest_value}"
                )
            
            case RollMode.DISADVANTAGE:
                smallest_value = min(self.dice[0].get_total(), self.dice[1].get_total())
                return(
                    f"🎲 **{prefix}:** {smallest_value}"
                )

    def build(self):
        if len(self.dice) == 1: # Single roll dice embed
            embed = discord.Embed(
                type="rich",
                description=self._get_description()
            )
            embed.set_author(
                name=self._get_title(),
                icon_url=self.avatar_url
            )

        elif len(self.dice) > 1: # Multiple roll dice embed
            description = ""
            for die in self.dice:
                description += f"{die}\n"

            embed = discord.Embed(
                type="rich",
                title=self._get_description(),
                description=description
            )
            embed.set_author(
                name=self._get_title(),
                icon_url=self.avatar_url
            )
        else:
            logging.error("Unknown dice amount in DiceEmbed.")
            return None

        embed.color = self._get_embed_color()
        return embed