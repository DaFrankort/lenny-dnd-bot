import random
import re
import discord
import sys
from discord.ext import commands
from enum import Enum

class Die:
    DIE_PATTERN = re.compile(r"^\s*(\d+)d(\d+)([+-]\d+)?\s*$", re.IGNORECASE)

    def __init__(self, die_notation: str):
        """Parses the die notation (e.g., '1d20+3') and initializes attributes."""
        match = self.DIE_PATTERN.match(die_notation)
        self.is_valid = bool(match)

        if not match:
            self.is_valid = False
            print(f" !!! Invalid die notation by user \"{die_notation}\" !!!")
            return

        self.die_notation = die_notation.lower()
        # TODO Add feedback when size limit was exceeded!
        self.num_rolls = min(int(match.group(1)), 256)
        self.die_sides = min(int(match.group(2)), 2048)
        self.modifier = min(int(match.group(3)), 2048) if match.group(3) else 0
        self.rolls = []

    def roll(self):
        """Internally rolls the die, use get_total() to get the result."""
        self.rolls = [random.randint(1, self.die_sides) for _ in range(self.num_rolls)]

    def get_total(self) -> int:
        """Returns the total of the rolled die + modifier"""
        if self.rolls is None:
            raise RuntimeError("No roll has been made yet! Call roll() before getting the total.")
        
        rolls_sum = min(sum(self.rolls), sys.maxsize) 
        return rolls_sum + self.modifier

    def __str__(self):
        """Returns a formatted string representation of the roll result."""
        if self.rolls is None:
            raise RuntimeError("No roll has been made yet! Call roll() first before attempting to print the die as string.")

        total_text = f"**{self.get_total()}**"
        rolls_text = f"({', '.join(map(str, self.rolls))})"
        modifier_text = f"{'+' if self.modifier > 0 else '-' if self.modifier < 0 else ''} {abs(self.modifier)}" if self.modifier else ""
        
        if len(self.rolls) != 1 or self.modifier:
            return f"{rolls_text} {modifier_text} => {total_text}"

        return total_text

class RollMode(Enum):
    NORMAL = "normal"
    ADVANTAGE = "advantage"
    DISADVANTAGE = "disadvantage"

class DiceEmbed:
    def __init__(self, ctx: commands.Context, dice: list[Die], reason: str | None,  mode: RollMode = RollMode.NORMAL):
        self.username = ctx.user.display_name.capitalize()
        self.avatar_url = ctx.user.avatar.url
        self.dice = dice
        self.reason = reason.capitalize() if reason is not None else reason
        self.mode = mode
        return
    
    def _get_embed_color(self):
        """Coding master Tomlolo's AMAZING code to get a hex value from a username.\n
        Turns the first 6 letters of a user's username into a hex-value for color.\n
        Outputs discord.Color
        """
        hex_value = ""
        hex_place = 0

        # This cute little function converts characters into unicode
        # I made it so the the alpha_value assignment line wouldn't be so hard to read
        def get_alpha(char):
            return ord(char.lower())-96

        while hex_place < 6:
            try:
                alpha_value = get_alpha(self.username[hex_place]) * get_alpha(self.username[hex_place + 1])
            except:
                # When username is shorter than 6 characters, inserts replacement value.
                alpha_value = 0 # Value can be changed to 255 for light and blue colors, 0 for dark and red colors.

            alpha_value = min(alpha_value, 255)
            if alpha_value < 16:
                hex_value = hex_value + "0" + hex(alpha_value)[2:]
            else:
                hex_value = hex_value + hex(alpha_value)[2:]

            hex_place += 2
        return discord.Color.from_str("#" + hex_value)
    
    def _get_title(self):
        match self.mode:
            case RollMode.NORMAL:
                return f"{self.username} rolled {self.dice[0].die_notation}!"
            
            case RollMode.ADVANTAGE:
                return f"{self.username} rolled {self.dice[0].die_notation} with advantage!"
            
            case RollMode.DISADVANTAGE:
                return f"{self.username} rolled {self.dice[0].die_notation} with disadvantage!"

    def _get_description(self):
        prefix = "Result" if self.reason is None else self.reason

        match self.mode:
            case RollMode.NORMAL:
                return f"🎲 {prefix}: {self.dice[0]}\n"
            
            case RollMode.ADVANTAGE:
                total1, total2 = self.dice[0].get_total(), self.dice[1].get_total()
                return (
                    f"{'✅' if total1 >= total2 else '🎲'} 1st {prefix}: {self.dice[0]}\n"
                    f"{'✅' if total2 >= total1 else '🎲'} 2nd {prefix}: {self.dice[1]}\n"
                )
            
            case RollMode.DISADVANTAGE:
                total1, total2 = self.dice[0].get_total(), self.dice[1].get_total()
                return(
                    f"{'✅' if total1 <= total2 else '🎲'} 1st {prefix}: {self.dice[0]}\n"
                    f"{'✅' if total2 <= total1 else '🎲'} 2nd {prefix}: {self.dice[1]}\n"
                )

    def build(self):
        embed = discord.Embed(
            type="rich",
            description=self._get_description()
            )
        embed.set_author(
            name=self._get_title(),
            icon_url=self.avatar_url
        )
        embed.color = self._get_embed_color()
        return embed