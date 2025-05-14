import logging
import os
from typing import List
import discord
from discord import app_commands
from discord import Interaction
from dotenv import load_dotenv

from dice import DiceExpression, DiceEmbed, RollMode
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
from initiative import (
    Initiative,
    InitiativeEmbed,
    InitiativeTracker,
    InitiativeTrackerEmbed,
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
    initiatives: InitiativeTracker

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
        self.initiatives = InitiativeTracker()

    def run_client(self):
        """Starts the bot using the token stored in .env"""
        super().run(self.token)

    async def on_ready(self):
        """Runs automatically when the bot is online"""
        print("----- INIT -----")
        logging.info(f"Logged in as {self.user} (ID: {self.user.id})")
        self._register_commands()
        await self._attempt_sync_guild()
        await self.tree.sync()
        print("----- READY -----")

    async def _attempt_sync_guild(self):
        guild = discord.utils.get(self.guilds, id=self.guild_id)
        if guild is None:
            logging.warning("Could not find guild, check .env for GUILD_ID")
        else:
            await self.tree.sync(guild=guild)
            logging.info(f"Connected to guild: {guild.name} (ID: {guild.id})")

    def _register_commands(self):
        def log_cmd(itr: Interaction):
            """Helper function to log user's command-usage in the terminal"""
            try:
                criteria = [f"[{k}={v}]" for k, v in vars(itr.namespace).items()]
            except Exception:
                criteria = []
            criteria_text = " ".join(criteria)

            logging.info(f"{itr.user.name} => /{itr.command.name} {criteria_text}")

        async def send_dice_message(
            itr: Interaction,
            expressions: list[DiceExpression] | DiceExpression,
            reason: str | None = None,
            mode: RollMode = RollMode.NORMAL,
        ):
            additional_message = ""
            if isinstance(expressions, DiceExpression):
                expressions = [expressions]  # Code requires expression as a list

            if not expressions[0].is_valid():
                await itr.response.send_message(
                    "❌ Something went wrong, please make sure to use the NdN or NdN+N format, ex: 2d6 / 1d4+1 ❌",
                    ephemeral=True,
                )
                return
            elif expressions[0].has_warnings():
                additional_message = expressions[0].get_warnings_text()

            embed = DiceEmbed(
                ctx=itr, expressions=expressions, reason=reason, mode=mode
            ).build()
            await itr.response.send_message(additional_message, embed=embed)

        @self.tree.command(name="roll", description="Roll your d20s!")
        async def roll(itr: Interaction, diceroll: str, reason: str = None):
            log_cmd(itr)
            expression = DiceExpression(diceroll)
            await send_dice_message(itr, expression, reason)

        @self.tree.command(name="d20", description="Just roll a clean d20")
        async def d20(itr: Interaction):
            log_cmd(itr)
            expression = DiceExpression("1d20")
            await send_dice_message(itr, expression)

        @self.tree.command(
            name="advantage", description="Lucky you! Roll and take the best of two!"
        )
        async def advantage(itr: Interaction, diceroll: str, reason: str = None):
            log_cmd(itr)
            expressions = [DiceExpression(diceroll), DiceExpression(diceroll)]
            await send_dice_message(itr, expressions, reason, RollMode.ADVANTAGE)

        @self.tree.command(
            name="disadvantage",
            description="Tough luck chump... Roll twice and suck it.",
        )
        async def disadvantage(itr: Interaction, diceroll: str, reason: str = None):
            log_cmd(itr)
            expressions = [DiceExpression(diceroll), DiceExpression(diceroll)]
            await send_dice_message(itr, expressions, reason, RollMode.DISADVANTAGE)

        @roll.autocomplete("reason")
        @advantage.autocomplete("reason")
        @disadvantage.autocomplete("reason")
        async def autocomplete_roll_reason(
            itr: Interaction, current: str
        ) -> List[app_commands.Choice[str]]:
            reasons = [
                "Attack",
                "Damage",
                "Initiative",
                "Saving Throw",
                "Athletics",
                "Acrobatics",
                "Sleight of Hand",
                "Stealth",
                "Arcana",
                "History",
                "Investigation",
                "Nature",
                "Religion",
                "Animal Handling",
                "Insight",
                "Medicine",
                "Perception",
                "Survival",
                "Deception",
                "Intimidation",
                "Performance",
                "Persuasion",
            ]
            filtered_reasons = [
                reason for reason in reasons if current.lower() in reason.lower()
            ]
            return [
                app_commands.Choice(name=reason, value=reason)
                for reason in filtered_reasons[:25]
            ]

        @self.tree.command(name="spell", description="Get the details for a spell.")
        async def spell(itr: Interaction, name: str):
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
        async def item(itr: Interaction, name: str):
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
        async def search(itr: Interaction, query: str):
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
        async def set_color(itr: Interaction, hex_color: str = ""):
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
        async def stats(itr: Interaction):
            log_cmd(itr)
            stats = Stats(itr)
            embed = StatsEmbed(stats)
            await itr.response.send_message(embed=embed)

        logging.info("Registered slash-commands.")

        @self.tree.command(
            name="initiative", description="Roll initiative for yourself or a creature."
        )
        async def initiative(
            itr: Interaction, modifier: int, target: str | None = None
        ):
            log_cmd(itr)
            initiative = Initiative(itr, modifier, target)
            self.initiatives.add(itr, initiative)
            await itr.response.send_message(embed=InitiativeEmbed(itr, initiative))

        @self.tree.command(
            name="showinitiative",
            description="Show an overview of all the rolled initiatives.",
        )
        async def show_initiative(itr: Interaction):
            log_cmd(itr)

            if self.initiatives.get(itr) == []:
                await itr.response.send_message(
                    f"❌ There are no initiatives for {itr.guild.name} ❌",
                    ephemeral=True,
                )
                return

            embed = InitiativeTrackerEmbed(itr, self.initiatives)
            await itr.response.send_message(embed=embed)

        @self.tree.command(
            name="clearinitiative", description="Clear all initiative rolls."
        )
        async def clear_initiative(itr: Interaction):
            log_cmd(itr)
            self.initiatives.clear(itr)
            await itr.response.send_message(
                f"❌ {itr.user.display_name} cleared Initiatives. ❌"
            )
