import logging
import os
import discord
from discord import app_commands
from discord import Interaction
from dotenv import load_dotenv
from commands.charactergen import NameGenCommand
from commands.color import ColorCommand
from commands.help import HelpCommand
from commands.initiative import InitiativeCommand
from commands.plansession import PlanSessionCommand
from commands.playsound import PlaySoundCommand
from commands.rolls import (
    AdvantageRollCommand,
    D20Command,
    DisadvantageRollCommand,
    RollCommand,
)
from commands.shortcut import ShortcutCommand
from commands.tokengen import TokenGenCommand, TokenGenUrlCommand
from context_menus.delete import DeleteContextMenu
from i18n import t

from commands.distribution import DistributionCommand
from commands.stats import StatsCommand

from dice import DiceExpression, DiceExpressionCache, DiceRollMode
from dnd import DNDData, DNDObject, Gender
from embeds import (
    NoResultsFoundEmbed,
    MultiDNDSelectView,
    SimpleEmbed,
    SuccessEmbed,
    UserActionEmbed,
)
from initiative import (
    InitiativeTracker,
)
from logger import log_cmd
from search import SearchEmbed, search_from_query
from voice_chat import VC, Sounds


class Bot(discord.Client):
    tree: app_commands.CommandTree
    token: str
    guild_id: int | None
    data: DNDData
    initiatives: InitiativeTracker
    voice_enabled: bool

    def __init__(self, voice: bool = True):
        load_dotenv()
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(
            intents=intents,
            status=discord.Status.do_not_disturb,  # Set to online in on_ready
        )

        self.tree = app_commands.CommandTree(self)
        self.token = os.getenv("DISCORD_BOT_TOKEN")

        guild_id = os.getenv("GUILD_ID")
        self.guild_id = int(guild_id) if guild_id is not None else None
        self.voice_enabled = voice

        self.data = DNDData()
        self.initiatives = InitiativeTracker()

    async def setup_hook(self):
        # Commands
        self.tree.add_command(DistributionCommand())
        self.tree.add_command(HelpCommand())
        self.tree.add_command(StatsCommand())
        self.tree.add_command(RollCommand())
        self.tree.add_command(AdvantageRollCommand())
        self.tree.add_command(DisadvantageRollCommand())
        self.tree.add_command(D20Command())
        self.tree.add_command(ShortcutCommand())
        self.tree.add_command(TokenGenCommand())
        self.tree.add_command(TokenGenUrlCommand())
        self.tree.add_command(InitiativeCommand(initiatives=self.initiatives))
        self.tree.add_command(PlanSessionCommand())
        self.tree.add_command(PlaySoundCommand())
        self.tree.add_command(ColorCommand())
        self.tree.add_command(NameGenCommand(data=self.data))

        # Context menus
        self.tree.add_command(DeleteContextMenu())

        await self.tree.sync()

    def run_client(self):
        """Starts the bot using the token stored in .env"""
        # log_handler set to None, as a handler is already added in main.py
        super().run(self.token, log_handler=None)

    async def on_ready(self):
        """Runs automatically when the bot is online"""
        logging.info("Initializing")
        logging.info(f"Logged in as {self.user} (ID: {self.user.id})")

        self._register_commands()
        await self._attempt_sync_guild()
        await self.tree.sync()
        Sounds.init_folders()
        VC.clean_temp_sounds()  # Files are often unused, clearing on launch cleans up storage.
        if self.voice_enabled:
            VC.check_ffmpeg()
        else:
            VC.disable_vc()

        await self.change_presence(
            activity=discord.CustomActivity(name="Rolling d20s!"),
            status=discord.Status.online,
        )
        logging.info("Finished initialization")

    async def _attempt_sync_guild(self):
        guild = discord.utils.get(self.guilds, id=self.guild_id)
        if guild is None:
            logging.warning("Could not find guild, check .env for GUILD_ID")
        else:
            await self.tree.sync(guild=guild)
            logging.info(f"Connected to guild: {guild.name} (ID: {guild.id})")

    def _register_commands(self):
        logging.info("Registered slash-commands")

        #
        # HELPER FUNCTIONS
        #

        async def send_DNDObject_lookup_result(
            itr: Interaction, label: str, found: list[DNDObject], name: str
        ):
            logging.debug(f"{label.upper()}: Found {len(found)} for '{name}'")

            if len(found) == 0:
                embed = NoResultsFoundEmbed(label, name)
                await itr.response.send_message(embed=embed, ephemeral=True)

            elif len(found) > 1:
                view = MultiDNDSelectView(name, found)
                await itr.response.send_message(view=view, ephemeral=True)

            else:
                embed = found[0].get_embed()
                view = embed.view
                if view:
                    await itr.response.send_message(embed=embed, view=view)
                    return
                await itr.response.send_message(embed=embed)

        #
        # COMMANDS
        #

        @self.tree.context_menu(name=t("contextmenu.reroll.name"))
        async def reroll(itr: Interaction, message: discord.Message):
            log_cmd(itr)
            if message.author.id != itr.client.user.id:
                await itr.response.send_message(
                    f"❌ Only works on dice-roll messages sent by {itr.client.user.name} ❌",
                    ephemeral=True,
                )
                return

            if not message.embeds or len(message.embeds) == 0:
                await itr.response.send_message(
                    "❌ Reroll doesn't work on this message type!", ephemeral=True
                )
                return

            embed = message.embeds[0]
            title = embed.author.name or ""
            if not ("Rolling" in title or "Re-rolling" in title):
                await itr.response.send_message(
                    "❌ Message does not contain a dice-roll!", ephemeral=True
                )
                return

            dice_notation = (
                title.replace("Rolling ", "").replace("Re-rolling", "").replace("!", "")
            )
            if "disadvantage" in dice_notation:
                # Check 'disadvantage' before 'advantage', may give a false positive otherwise.
                mode = DiceRollMode.Disadvantage
                dice_notation = dice_notation.replace("with disadvantage", "")
            elif "advantage" in dice_notation:
                mode = DiceRollMode.Advantage
                dice_notation = dice_notation.replace("with advantage", "")
            else:
                mode = DiceRollMode.Normal
            dice_notation = dice_notation.strip()

            reason = None
            if "Result" not in embed.fields[0].value:
                lines = embed.fields[0].value.strip().splitlines()
                for line in lines:
                    if line.startswith("🎲") and ":" in line:
                        label = (
                            line[1:].split(":", 1)[0].strip()
                        )  # Remove 🎲 and split before colon
                        reason = label.replace("*", "")
                        break

            expression = DiceExpression(
                expression=dice_notation, mode=mode, reason=reason
            )
            expression.title = expression.title.replace("Rolling", "Re-rolling")
            DiceExpressionCache.store_expression(itr, expression, dice_notation)

            await itr.response.send_message(
                embed=UserActionEmbed(
                    itr=itr,
                    title=expression.title,
                    description=expression.description,
                ),
                ephemeral=expression.ephemeral,
            )
            await VC.play_dice_roll(itr, expression, reason)

        @self.tree.command(
            name=t("commands.spell.name"), description=t("commands.spell.desc")
        )
        async def spell(itr: Interaction, name: str):
            log_cmd(itr)
            found = self.data.spells.get(name)
            await send_DNDObject_lookup_result(itr, "spells", found, name)

        @spell.autocomplete("name")
        async def spell_autocomplete(
            itr: discord.Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            return self.data.spells.get_autocomplete_suggestions(query=current)

        @self.tree.command(
            name=t("commands.item.name"), description=t("commands.item.desc")
        )
        async def item(itr: Interaction, name: str):
            log_cmd(itr)
            found = self.data.items.get(name)
            await send_DNDObject_lookup_result(itr, "items", found, name)

        @item.autocomplete("name")
        async def item_autocomplete(
            itr: discord.Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            return self.data.items.get_autocomplete_suggestions(query=current)

        @self.tree.command(
            name=t("commands.condition.name"),
            description=t("commands.condition.desc"),
        )
        async def condition(itr: Interaction, name: str):
            log_cmd(itr)
            found = self.data.conditions.get(name)
            await send_DNDObject_lookup_result(itr, "conditions", found, name)

        @condition.autocomplete("name")
        async def condition_autocomplete(
            itr: discord.Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            return self.data.conditions.get_autocomplete_suggestions(query=current)

        @self.tree.command(
            name=t("commands.creature.name"),
            description=t("commands.creature.desc"),
        )
        async def creature(itr: Interaction, name: str):
            log_cmd(itr)
            found = self.data.creatures.get(name)
            await send_DNDObject_lookup_result(itr, "creatures", found, name)

        @creature.autocomplete("name")
        async def creature_autocomplete(
            itr: discord.Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            return self.data.creatures.get_autocomplete_suggestions(query=current)

        @self.tree.command(
            name=t("commands.class.name"),
            description=t("commands.class.desc"),
        )
        async def character_class(itr: Interaction, name: str):
            log_cmd(itr)
            found = self.data.classes.get(name)
            await send_DNDObject_lookup_result(itr, "classes", found, name)

        @character_class.autocomplete("name")
        async def character_class_autocomplete(
            itr: discord.Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            return self.data.classes.get_autocomplete_suggestions(query=current)

        @self.tree.command(
            name=t("commands.rule.name"), description=t("commands.rule.desc")
        )
        async def rule(itr: Interaction, name: str):
            log_cmd(itr)
            found = self.data.rules.get(name)
            await send_DNDObject_lookup_result(itr, "rules", found, name)

        @rule.autocomplete("name")
        async def rule_autocomplete(
            itr: discord.Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            return self.data.rules.get_autocomplete_suggestions(query=current)

        @self.tree.command(
            name=t("commands.action.name"), description=t("commands.action.desc")
        )
        async def action(itr: Interaction, name: str):
            log_cmd(itr)
            found = self.data.actions.get(name)
            await send_DNDObject_lookup_result(itr, "actions", found, name)

        @action.autocomplete("name")
        async def action_autocomplete(
            itr: discord.Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            return self.data.actions.get_autocomplete_suggestions(query=current)

        @self.tree.command(
            name=t("commands.feat.name"),
            description=t("commands.feat.desc"),
        )
        async def feat(itr: Interaction, name: str):
            log_cmd(itr)
            found = self.data.feats.get(name)
            await send_DNDObject_lookup_result(itr, "feats", found, name)

        @feat.autocomplete("name")
        async def feat_autocomplete(
            itr: discord.Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            return self.data.feats.get_autocomplete_suggestions(query=current)

        @self.tree.command(
            name=t("commands.language.name"),
            description=t("commands.language.desc"),
        )
        async def language(itr: Interaction, name: str):
            log_cmd(itr)
            found = self.data.languages.get(name)
            await send_DNDObject_lookup_result(itr, "languages", found, name)

        @language.autocomplete("name")
        async def language_autocomplete(
            itr: discord.Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            return self.data.languages.get_autocomplete_suggestions(query=current)

        @self.tree.command(
            name=t("commands.background.name"),
            description=t("commands.background.desc"),
        )
        async def background(itr: Interaction, name: str):
            log_cmd(itr)
            found = self.data.backgrounds.get(name)
            await send_DNDObject_lookup_result(itr, "background", found, name)

        @background.autocomplete("name")
        async def background_autocomplete(
            itr: discord.Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            return self.data.backgrounds.get_autocomplete_suggestions(query=current)

        @self.tree.command(
            name=t("commands.table.name"),
            description=t("commands.table.desc"),
        )
        async def table(itr: Interaction, name: str):
            log_cmd(itr)
            found = self.data.tables.get(name)
            await send_DNDObject_lookup_result(itr, "table", found, name)

        @table.autocomplete("name")
        async def table_autocomplete(
            itr: discord.Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            return self.data.tables.get_autocomplete_suggestions(query=current)

        @self.tree.command(
            name=t("commands.species.name"),
            description=t("commands.species.desc"),
        )
        async def species(itr: Interaction, name: str):
            log_cmd(itr)
            found = self.data.species.get(name)
            await send_DNDObject_lookup_result(itr, "species", found, name)

        @species.autocomplete("name")
        async def species_autocomplete(
            itr: discord.Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            return self.data.species.get_autocomplete_suggestions(query=current)

        @self.tree.command(
            name=t("commands.search.name"), description=t("commands.search.desc")
        )
        async def search(itr: Interaction, query: str):
            log_cmd(itr)
            results = search_from_query(query, self.data)
            logging.debug(f"Found {len(results.get_all())} results for '{query}'")

            if len(results.get_all()) == 0:
                embed = NoResultsFoundEmbed("results", query)
                await itr.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = SearchEmbed(query, results)
                await itr.response.send_message(
                    embed=embed, view=embed.view, ephemeral=True
                )
