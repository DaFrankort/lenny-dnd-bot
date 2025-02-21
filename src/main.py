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
    if not dice.is_valid:
        await ctx.response.send_message('⚠️ Format has to be NdN or NdN+N, ex: 2d6 / 1d4+1 ⚠️', ephemeral=True)
        return

    dice.roll()
    response = (
        f"🎲 Roll! ``{diceroll.lower()}``\n"
        f"Roll: {dice}\n"
    )
    await ctx.response.send_message(response)


@cmd_tree.command(
    name="advantage",
    description="Lucky you! Roll and take the best of two!",
)
async def advantage(ctx, diceroll: str):
    dices = [Dice(diceroll), Dice(diceroll)]
    if not dices[0].is_valid:
        await ctx.response.send_message('⚠️ Format has to be NdN or NdN+N, ex: 2d6 / 1d4+1 ⚠️', ephemeral=True)
        return
    
    for dice in dices:
        dice.roll()
    
    total1, total2 = dices[0].get_total(), dices[1].get_total()
    best_total = max(total1, total2)

    response = (
        f"🎲 Advantage Roll! ``{diceroll.lower()}``\n"
        f"Roll 1: {dices[0]}\n"
        f"Roll 2: {dices[1]}\n"
        f"✅ Best Roll: **{best_total}**"
    )
    await ctx.response.send_message(response)


@cmd_tree.command(
    name="disadvantage",
    description="Tough luck chump... Roll twice and suck it.",
)
async def disadvantage(ctx, diceroll: str):
    dices = [Dice(diceroll), Dice(diceroll)]
    if not dices[0].is_valid:
        await ctx.response.send_message('⚠️ Format has to be NdN or NdN+N, ex: 2d6 / 1d4+1 ⚠️', ephemeral=True)
        return
    
    for dice in dices:
        dice.roll()
    
    total1, total2 = dices[0].get_total(), dices[1].get_total()
    worst_total = min(total1, total2)

    response = (
        f"🎲 Disadvantage Roll! ``{diceroll.lower()}`` \n"
        f"Roll 1: {dices[0]}\n"
        f"Roll 2: {dices[1]}\n"
        f"✅ Worst Roll: **{worst_total}**"
    )
    await ctx.response.send_message(response)


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
