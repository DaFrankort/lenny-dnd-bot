import random
import re
import discord
import os
from dice import Dice
from spells import Spells, pretty_response_spell
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# Init
load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")
guild_id = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = discord.Client(intents=intents)
cmd_tree = app_commands.CommandTree(bot)

# Dictionaries
spells = Spells("./submodules/5etools-src/data/spells")


# Slash commands
@cmd_tree.command(
    name="roll",
    description="Roll your d20s!",
)
async def roll(ctx, diceroll: str):
    dice = Dice(diceroll)

    # TODO: Send error to user if wrong syntax
    # if dice is None:
    #     await ctx.response.send_message('⚠️ Format has to be NdN, ex: 1d4. ⚠️', ephemeral=True)
    #     return

    result = dice.roll()
    await ctx.response.send_message(result)


@cmd_tree.command(
    name="advantage",
    description="Lucky you! Roll and take the best of two!",
)
async def advantage(ctx, diceroll: str):
    dice = Dice(diceroll)
    # TODO: Send error to user if wrong syntax
    result = max(dice.roll(), dice.roll())
    await ctx.response.send_message(result)
    return


@cmd_tree.command(
    name="disadvantage",
    description="Tough luck chump... Roll twice and suck it.",
)
async def disadvantage(ctx, diceroll: str):
    dice = Dice(diceroll)
    # TODO: Send error to user if wrong syntax
    result = min(dice.roll(), dice.roll())
    await ctx.response.send_message(result)
    return


@cmd_tree.command(name="spell", description="Search for a spell.")
async def search_spell(ctx, name: str):
    found = spells.search_spell(name)
    await pretty_response_spell(ctx, found)
    return


# Run
@bot.event
async def on_ready():
    guild = bot.get_guild(guild_id)
    if guild is None:
        print("HELP, CAN'T GET GUILD")
    else:
        print(guild.name)
    await cmd_tree.sync(guild=guild)
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")


bot.run(token)
