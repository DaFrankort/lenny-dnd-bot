import discord
import hashlib
from discord.ext import commands

def _get_color_from_username(ctx: commands.Context):
    # TODO Logic is functional but tom wanted to whip something up, so I deactivated this logic to not shatter his pride.
    # username = ctx.message.author.display_name
    # hex_color = hashlib.sha256(username.encode()).hexdigest()[:6]

    hex_color = "ffffff"
    return discord.Color.from_str("#" + hex_color)

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
    embed.color = _get_color_from_username(ctx)

    return embed