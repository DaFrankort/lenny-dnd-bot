import discord
import hashlib
from discord.ext import commands

def _get_color_from_username(username: str):
    """Coding master Tomlolo's AMAZING code to get a hex value from a username."""
    # The number of username characters to encode is hardcoded to 6
    hex_value = ""
    hex_place = 0

    # This cute little function converts characters into unicode
    # I made it so the the alpha_value assignment line wouldn't be so hard to read
    def get_alpha(char):
        return ord(char.lower())-96

    while hex_place < 6:
        try:
            alpha_value = get_alpha(username[hex_place]) * get_alpha(username[hex_place + 1])
        except:
            alpha_value = 0 # Change this value to 255 if you want, read comments below for instruction

        # The above exception is here to prevent crashing if a username is less than 6 characters long,
        # thus allowing the rest of the function to fill the function output with with "0"

        # For example:
        # If the username is == "Tomlolo", the output is "2c9cb4"
        # If the username is "Dark", the output is "04c600"
        # If the username is blank, or "", the output is "000000"

        # This results in short names being dark and red
        # If you want them to be light and blue, replace the alpha_value exception from 0 to 255
        if alpha_value > 255:
            alpha_value = alpha_value & 255
        if alpha_value < 16:
            hex_value = hex_value + "0" + hex(alpha_value)[2:]
        else:
            hex_value = hex_value + hex(alpha_value)[2:]
    
        hex_place = hex_place + 2     
    return discord.Color.from_str("#" + hex_value)

# TODO Discuss if we want to do embeds this way, lol
def get_roll_embed(ctx: commands.Context, title: str, description: str):
    embed = discord.Embed(
        type="rich",
        description=description
        )
    embed.set_author(
        name=title,
        icon_url=ctx.user.avatar.url
    )
    embed.color = _get_color_from_username(ctx.user.display_name)

    return embed