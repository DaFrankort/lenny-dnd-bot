import logging
import discord
import os
from dice import Dice, DiceEmbed, RollMode
from spells import MultiSpellSelect, MultiSpellSelectView, NoSpellsFoundEmbed, SpellEmbed, SpellList
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from user_colors import UserColor, ColorEmbed

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
spells = SpellList("./submodules/5etools-src/data/spells")


# Slash commands
@cmd_tree.command(name="roll", description="Roll your d20s!")
async def roll(ctx: commands.Context, diceroll: str, reason: str = None):
    print(f"{ctx.user.name} => /roll {diceroll} {reason if reason else ''}")
    die = Dice(diceroll)
    if not die.is_valid:
        await ctx.response.send_message('⚠️ Format has to be NdN or NdN+N, ex: 2d6 / 1d4+1 ⚠️', ephemeral=True)
        return

    embed = DiceEmbed(ctx=ctx, dice=[die], reason=reason).build()
    await ctx.response.send_message(embed=embed)


@cmd_tree.command(name="advantage", description="Lucky you! Roll and take the best of two!")
async def advantage(ctx: commands.Context, diceroll: str, reason: str = None):
    print(f"{ctx.user.name} => /advantage {diceroll} {reason if reason else ''}")
    dice = [Dice(diceroll), Dice(diceroll)]
    if not dice[0].is_valid:
        await ctx.response.send_message('⚠️ Format has to be NdN or NdN+N, ex: 2d6 / 1d4+1 ⚠️', ephemeral=True)
        return
    
    embed = DiceEmbed(ctx=ctx, dice=dice, reason=reason, mode=RollMode.ADVANTAGE).build()
    await ctx.response.send_message(embed=embed)


@cmd_tree.command(name="disadvantage", description="Tough luck chump... Roll twice and suck it.")
async def disadvantage(ctx: commands.Context, diceroll: str, reason: str = None):
    print(f"{ctx.user.name} => /disadvantage {diceroll} {reason if reason else ''}")
    dice = [Dice(diceroll), Dice(diceroll)]
    if not dice[0].is_valid:
        await ctx.response.send_message('⚠️ Format has to be NdN or NdN+N, ex: 2d6 / 1d4+1 ⚠️', ephemeral=True)
        return
    
    embed = DiceEmbed(ctx=ctx, dice=dice, reason=reason, mode=RollMode.DISADVANTAGE).build()
    await ctx.response.send_message(embed=embed)


@cmd_tree.command(name="spell", description="Get the details for a spell.")
async def spell(ctx: discord.Interaction, name: str):
    logging.info(f"{ctx.user.name} => /spell {name}")
    found = spells.get(name)
    logging.debug(f"Found {len(found)} for '{name}'")

    if len(found) == 0:
        embed = NoSpellsFoundEmbed(name)
        await ctx.response.send_message(embed=embed)
    
    elif len(found) > 1:
        view = MultiSpellSelectView(name, found)
        await ctx.response.send_message(view=view)

    else:
        embed = SpellEmbed(found[0])
        await ctx.response.send_message(embed=embed)
        

@cmd_tree.command(name="search", description="Search for a spell.")
async def spell(ctx: discord.Interaction, query: str):
    logging.info(f"{ctx.user.name} => /search {query}")
    found = spells.search(query)

    if len(found) == 0:
        embed = NoSpellsFoundEmbed(query)
        await ctx.response.send_message(embed=embed)
    else:
        view = MultiSpellSelectView(query, found)
        await ctx.response.send_message(view=view)


@cmd_tree.command(name="color", description="Set a preferred color using a hex-value. Leave hex_color empty to use auto-generated colors.")
async def set_color(itr: discord.Interaction, hex_color: str = ""):
    print(f"{itr.user.name} => /color {hex_color}")
    if hex_color == '':
        removed = UserColor.remove(itr.user.id)
        message = "❌ Cleared user-defined color. ❌" if removed else "⚠️ You have not yet set a color. ⚠️"
        await itr.response.send_message(message, ephemeral=True)
        return

    user_color = UserColor(itr=itr, hex_value=hex_color)
    if not user_color.is_valid:
        await itr.response.send_message('⚠️ Invalid hex value: Must be 6 valid hexadecimal characters (0-9, A-F), optionally starting with a # symbol. (eg. ff00ff / #ff00ff) ⚠️', ephemeral=True)
        return
    user_color.save()

    embed = ColorEmbed(itr=itr, user_color=user_color).build()
    await itr.response.send_message(embed=embed, ephemeral=True)


# Run
@bot.event
async def on_ready():
    print("------ INIT ------")

    if not os.path.exists("temp"):
        os.mkdir("temp")

    guild = bot.get_guild(guild_id)
    if guild is None:
        print("HELP, CAN'T GET GUILD")
    else:
        await cmd_tree.sync(guild=guild)
        print(guild.name)
    
    await cmd_tree.sync()
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------ READY ------")

bot.run(token)