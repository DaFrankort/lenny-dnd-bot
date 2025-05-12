import logging
import os
import discord
from discord import app_commands
from dotenv import load_dotenv

from dice2 import DiceExpression, DiceEmbed, DiceRollMode
from dnd import SpellList, ItemList
from embeds import (
    ItemEmbed,
    MultiItemSelectView,
    MultiSpellSelectView,
    NoItemsFoundEmbed,
    NoSpellsFoundEmbed,
    NoSearchResultsFoundEmbed,
    SpellEmbed,
)
from search import SearchEmbed, search_from_query
from stats import Stats, StatsEmbed
from user_colors import UserColor, ColorEmbed


class Bot(discord.Client):
    tree: app_commands.CommandTree
    token: str
    guild_id: int
    spells: SpellList
    items: ItemList

    def __init__(self):
        load_dotenv()
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)
        self.token = os.getenv("DISCORD_BOT_TOKEN")
        self.guild_id = int(os.getenv("GUILD_ID"))

        self.spells = SpellList()
        self.items = ItemList()

    def run_client(self):
        """Starts the bot using the token stored in .env"""
        super().run(self.token)

    async def on_ready(self):
        """Runs automatically when the bot is online"""
        print("----- INIT -----")
        logging.info(f"Logged in as {self.user} (ID: {self.user.id})")
        self._register_commands()
        await self._attempt_sync_guild()
        print("----- READY -----")

    async def _attempt_sync_guild(self):
        guild = discord.utils.get(self.guilds, id=self.guild_id)
        if guild is None:
            logging.warning("Could not find guild, check .env for GUILD_ID")
        else:
            await self.tree.sync(guild=guild)
            logging.info(f"Connected to guild: {guild.name} (ID: {guild.id})")

    def _register_commands(self):
        def log_cmd(itr: discord.Interaction):
            """Helper function to log user's command-usage in the terminal"""
            try:
                criteria = [f"[{k}={v}]" for k, v in vars(itr.namespace).items()]
            except Exception:
                criteria = []
            criteria_text = " ".join(criteria)

            logging.info(f"{itr.user.name} => /{itr.command.name} {criteria_text}")

        @self.tree.command(name="roll", description="Roll your d20s!")
        async def roll(itr: discord.Interaction, diceroll: str, reason: str = None):
            log_cmd(itr)
            # TODO reason
            expression = DiceExpression(diceroll, DiceRollMode.Normal)
            return await itr.response.send_message(embed=DiceEmbed(expression))

        @self.tree.command(name="d20", description="Just roll a clean d20")
        async def d20(itr: discord.Interaction):
            log_cmd(itr)
            expression = DiceExpression("1d20", DiceRollMode.Normal)
            return await itr.response.send_message(embed=DiceEmbed(expression))

        @self.tree.command(
            name="advantage", description="Lucky you! Roll and take the best of two!"
        )
        async def advantage(
            itr: discord.Interaction, diceroll: str, reason: str = None
        ):
            log_cmd(itr)
            expression = DiceExpression(diceroll, DiceRollMode.Advantage)
            return await itr.response.send_message(embed=DiceEmbed(expression))

        @self.tree.command(
            name="disadvantage",
            description="Tough luck chump... Roll twice and suck it.",
        )
        async def disadvantage(
            itr: discord.Interaction, diceroll: str, reason: str = None
        ):
            log_cmd(itr)
            expression = DiceExpression(diceroll, DiceRollMode.Disadvantage)
            return await itr.response.send_message(embed=DiceEmbed(expression))

        @self.tree.command(name="spell", description="Get the details for a spell.")
        async def spell(itr: discord.Interaction, name: str):
            log_cmd(itr)
            found = self.spells.get(name)
            logging.debug(f"Found {len(found)} for '{name}'")

            if len(found) == 0:
                embed = NoSpellsFoundEmbed(name)
                await itr.response.send_message(embed=embed)

            elif len(found) > 1:
                view = MultiSpellSelectView(name, found)
                await itr.response.send_message(view=view, ephemeral=True)

            else:
                embed = SpellEmbed(found[0])
                await itr.response.send_message(embed=embed)

        @self.tree.command(name="item", description="Get the details for an item.")
        async def item(itr: discord.Interaction, name: str):
            log_cmd(itr)
            found = self.items.get(name)
            logging.debug(f"Found {len(found)} for '{name}'")

            if len(found) == 0:
                embed = NoItemsFoundEmbed(name)
                await itr.response.send_message(embed=embed)

            elif len(found) > 1:
                view = MultiItemSelectView(name, found)
                await itr.response.send_message(view=view, ephemeral=True)

            else:
                embed = ItemEmbed(found[0])
                await itr.response.send_message(embed=embed)

        @self.tree.command(name="search", description="Search for a spell.")
        async def search(itr: discord.Interaction, query: str):
            log_cmd(itr)
            found_spells, found_items = search_from_query(
                query, self.spells, self.items
            )
            logging.debug(
                f"Found {len(found_spells)} spells and {len(found_items)} for '{query}'"
            )

            if len(found_spells) + len(found_items) == 0:
                embed = NoSearchResultsFoundEmbed(query)
                await itr.response.send_message(embed=embed)
            else:
                embed = SearchEmbed(query, found_spells, found_items)
                await itr.response.send_message(embed=embed, view=embed.view)

        @self.tree.command(
            name="color",
            description="Set a preferred color using a hex-value. Leave hex_color empty to use auto-generated colors.",
        )
        async def set_color(itr: discord.Interaction, hex_color: str = ""):
            log_cmd(itr)
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

        @self.tree.command(
            name="stats",
            description="Roll stats for a new character, using the 4d6 drop lowest method.",
        )
        async def stats(itr: discord.Interaction):
            log_cmd(itr)
            stats = Stats(itr)
            embed = StatsEmbed(stats)
            await itr.response.send_message(embed=embed)

        logging.info("Registered slash-commands.")
