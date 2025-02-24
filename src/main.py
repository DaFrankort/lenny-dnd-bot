import discord
import os
from dice import Dice, DiceEmbed, RollMode
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
async def roll(ctx: commands.Context, diceroll: str):
    print(f"{ctx.user.name} => /roll {diceroll}")
    dice = Dice(diceroll)
    if not dice.is_valid:
        await ctx.response.send_message('⚠️ Format has to be NdN or NdN+N, ex: 2d6 / 1d4+1 ⚠️', ephemeral=True)
        return

    dice.roll()

    embed = DiceEmbed(ctx=ctx, dices=[dice]).build()
    await ctx.response.send_message(embed=embed)


@cmd_tree.command(
    name="advantage",
    description="Lucky you! Roll and take the best of two!",
)
async def advantage(ctx: commands.Context, diceroll: str):
    print(f"{ctx.user.name} => /advantage {diceroll}")
    dices = [Dice(diceroll), Dice(diceroll)]
    if not dices[0].is_valid:
        await ctx.response.send_message('⚠️ Format has to be NdN or NdN+N, ex: 2d6 / 1d4+1 ⚠️', ephemeral=True)
        return
    
    for dice in dices:
        dice.roll()
    
    embed = DiceEmbed(ctx=ctx, dices=dices, mode=RollMode.ADVANTAGE).build()
    await ctx.response.send_message(embed=embed)


@cmd_tree.command(
    name="disadvantage",
    description="Tough luck chump... Roll twice and suck it.",
)
async def disadvantage(ctx: commands.Context, diceroll: str):
    print(f"{ctx.user.name} => /disadvantage {diceroll}")
    dices = [Dice(diceroll), Dice(diceroll)]
    if not dices[0].is_valid:
        await ctx.response.send_message('⚠️ Format has to be NdN or NdN+N, ex: 2d6 / 1d4+1 ⚠️', ephemeral=True)
        return
    
    for dice in dices:
        dice.roll()
    
    embed = DiceEmbed(ctx=ctx, dices=dices, mode=RollMode.DISADVANTAGE).build()
    await ctx.response.send_message(embed=embed)


@cmd_tree.command(name="spell", description="Search for a spell.")
async def search_spell(ctx, name: str):
    print(f"{ctx.user.name} => /spell {name}")
    found = spells.search_spell(name)
    await pretty_response_spell(ctx, found)
    return


# Run
@bot.event
async def on_ready():
    print("------ INIT ------")
    guild = bot.get_guild(guild_id)
    if guild is None:
        print("HELP, CAN'T GET GUILD")
    else:
        print(guild.name)
    await cmd_tree.sync(guild=guild)
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------ READY ------")

bot.run(token)
