import random
import re
import discord
import os
from dice import Dice
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# Init
load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = discord.Client(intents=intents)
cmd_tree = app_commands.CommandTree(bot)

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
async def advantage(ctx, dice: str):
    #TODO - double dice roll and return best result
    await ctx.response.send_message("Oopsie not working yet")
    return

@cmd_tree.command(
    name="disadvantage",
    description="Tough luck chump... Roll twice and suck it.",
)
async def disadvantage(ctx, dice: str):
    #TODO - double dice roll and return worst result
    await ctx.response.send_message("Oopsie not working yet")
    return

# Run
@bot.event
async def on_ready():
    await cmd_tree.sync()
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

bot.run(token)

