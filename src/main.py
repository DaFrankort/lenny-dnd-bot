import argparse
import logging
import discord
import os
from dice import DiceExpression, DiceEmbed, RollMode
from dnd import ItemList, SpellList
from embeds import (
    ItemEmbed,
    MultiItemSelectView,
    MultiSpellSelectView,
    NoItemsFoundEmbed,
    NoSearchResultsFoundEmbed,
    NoSpellsFoundEmbed,
    SpellEmbed,
)
from search import SearchEmbed, search_from_query
from discord import app_commands
from dotenv import load_dotenv
from stats import Stats, StatsEmbed
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

logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG to see all messages, normal is INFO
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],  # Output to console
)

# Dictionaries
spells = SpellList()
items = ItemList()


# Slash commands
@cmd_tree.command(name="roll", description="Roll your d20s!")
async def roll(ctx: discord.Interaction, diceroll: str, reason: str = None):
    logging.info(f"{ctx.user.name} => /roll {diceroll} {reason if reason else ''}")
    additional_message = ""

    expression = DiceExpression(diceroll)
    if not expression.is_valid():
        await ctx.response.send_message(
            "❌ Something went wrong, please make sure to use the NdN or NdN+N format, ex: 2d6 / 1d4+1 ❌",
            ephemeral=True,
        )
        return
    elif expression.has_warnings():
        additional_message = expression.get_warnings_text()

    embed = DiceEmbed(ctx=ctx, expressions=[expression], reason=reason).build()
    await ctx.response.send_message(additional_message, embed=embed)


@cmd_tree.command(name="d20", description="Just roll a clean d20")
async def d20(ctx: discord.Interaction):
    logging.info(f"{ctx.user.name} => /d20")
    expression = DiceExpression("1d20")

    embed = DiceEmbed(ctx=ctx, expressions=[expression]).build()
    await ctx.response.send_message(embed=embed)


@cmd_tree.command(
    name="advantage", description="Lucky you! Roll and take the best of two!"
)
async def advantage(ctx: discord.Interaction, diceroll: str, reason: str = None):
    logging.info(f"{ctx.user.name} => /advantage {diceroll} {reason if reason else ''}")
    additional_message = ""

    expressions = [DiceExpression(diceroll), DiceExpression(diceroll)]
    if not expressions[0].is_valid():
        await ctx.response.send_message(
            "❌ Something went wrong, please make sure to use the NdN or NdN+N format, ex: 2d6 / 1d4+1 ❌",
            ephemeral=True,
        )
        return
    elif expressions[0].has_warnings():
        additional_message = expressions[0].get_warnings_text()

    embed = DiceEmbed(
        ctx=ctx, expressions=expressions, reason=reason, mode=RollMode.ADVANTAGE
    ).build()
    await ctx.response.send_message(additional_message, embed=embed)


@cmd_tree.command(
    name="disadvantage", description="Tough luck chump... Roll twice and suck it."
)
async def disadvantage(ctx: discord.Interaction, diceroll: str, reason: str = None):
    logging.info(
        f"{ctx.user.name} => /disadvantage {diceroll} {reason if reason else ''}"
    )
    additional_message = ""

    expressions = [DiceExpression(diceroll), DiceExpression(diceroll)]
    if not expressions[0].is_valid():
        await ctx.response.send_message(
            "❌ Something went wrong, please make sure to use the NdN or NdN+N format, ex: 2d6 / 1d4+1 ❌",
            ephemeral=True,
        )
        return
    elif expressions[0].has_warnings():
        additional_message = expressions[0].get_warnings_text()

    embed = DiceEmbed(
        ctx=ctx, expressions=expressions, reason=reason, mode=RollMode.DISADVANTAGE
    ).build()
    await ctx.response.send_message(additional_message, embed=embed)


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
        await ctx.response.send_message(view=view, ephemeral=True)

    else:
        embed = SpellEmbed(found[0])
        await ctx.response.send_message(embed=embed)


@cmd_tree.command(name="item", description="Get the details for an item.")
async def item(ctx: discord.Interaction, name: str):
    logging.info(f"{ctx.user.name} => /item {name}")
    found = items.get(name)
    logging.debug(f"Found {len(found)} for '{name}'")

    if len(found) == 0:
        embed = NoItemsFoundEmbed(name)
        await ctx.response.send_message(embed=embed)

    elif len(found) > 1:
        view = MultiItemSelectView(name, found)
        await ctx.response.send_message(view=view, ephemeral=True)

    else:
        embed = ItemEmbed(found[0])
        await ctx.response.send_message(embed=embed)


@cmd_tree.command(name="search", description="Search for a spell.")
async def search(ctx: discord.Interaction, query: str):
    logging.info(f"{ctx.user.name} => /search {query}")
    found_spells, found_items = search_from_query(query, spells, items)
    logging.debug(
        f"Found {len(found_spells)} spells and {len(found_items)} for '{query}'"
    )

    if len(found_spells) + len(found_items) == 0:
        embed = NoSearchResultsFoundEmbed(query)
        await ctx.response.send_message(embed=embed)
    else:
        embed = SearchEmbed(query, found_spells, found_items)
        await ctx.response.send_message(embed=embed, view=embed.view)


@cmd_tree.command(
    name="color",
    description="Set a preferred color using a hex-value. Leave hex_color empty to use auto-generated colors.",
)
async def set_color(itr: discord.Interaction, hex_color: str = ""):
    logging.info(f"{itr.user.name} => /color {hex_color}")
    if hex_color == "":
        removed = UserColor.remove(itr)
        message = (
            "❌ Cleared user-defined color. ❌"
            if removed
            else "⚠️ You have not yet set a color. ⚠️"
        )
        await itr.response.send_message(message, ephemeral=True)
        return

    if not UserColor.validate(hex_color):
        await itr.response.send_message(
            "⚠️ Invalid hex value: Must be 6 valid hexadecimal characters (0-9, A-F), optionally starting with a # symbol. (eg. ff00ff / #ff00ff) ⚠️",
            ephemeral=True,
        )
        return

    color = UserColor.parse(hex_color)
    UserColor.save(itr, color)

    embed = ColorEmbed(itr=itr, hex_color=hex_color)
    await itr.response.send_message(embed=embed, ephemeral=True)


@cmd_tree.command(
    name="stats",
    description="Roll stats for a new character, using the 4d6 drop lowest method.",
)
async def stats(itr: discord.Interaction):
    logging.info(f"{itr.user.name} => /stats")
    stats = Stats(itr)
    embed = StatsEmbed(stats)
    await itr.response.send_message(embed=embed)


# Run
@bot.event
async def on_ready():
    print("------ INIT ------")

    if not os.path.exists("temp"):
        os.mkdir("temp")

    guild = bot.get_guild(guild_id)
    if guild is None:
        logging.warning("HELP, CAN'T GET GUILD")
    else:
        await cmd_tree.sync(guild=guild)
        logging.info(f"Connected to guild: {guild.name} (ID: {guild.id})")

    await cmd_tree.sync()

    logging.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------ READY ------")


def check_support(spells: SpellList):
    sorted_spells = sorted(spells.spells, key=lambda s: s.name)
    unsupported = False

    for spell in sorted_spells:
        if "Unsupported" in spell.casting_time:
            logging.warning(f"{spell.name}: {spell.casting_time}")
            unsupported = True
        if "Unsupported" in spell.duration:
            logging.warning(f"{spell.name}: {spell.duration}")
            unsupported = True
        if "Unsupported" in spell.spell_range:
            logging.warning(f"{spell.name}: {spell.spell_range}")
            unsupported = True

        for _, desc in spell.descriptions:
            if "Unsupported" in desc:
                logging.warning(f"{spell.name}: {desc}")
                unsupported = True

    if not unsupported:
        logging.info("No unsupported spells found!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check-support",
        type=bool,
        default=False,
        action=argparse.BooleanOptionalAction,
    )

    args = parser.parse_args()

    if args.check_support:
        check_support(spells)
    else:
        bot.run(token)
