import logging
import os

import discord
from discord import app_commands
from dotenv import load_dotenv

from commands.charactergen import CharacterGenCommand
from commands.color import ColorCommandGroup
from commands.config import ConfigCommand
from commands.distribution import DistributionCommand
from commands.help import HelpCommand
from commands.homebrew import HomebrewCommandGroup
from commands.initiative import InitiativeCommand
from commands.namegen import NameGenCommand
from commands.plansession import PlanSessionCommand
from commands.playsound import PlaySoundCommand
from commands.profile import ProfileCommandGroup
from commands.roll import (
    AdvantageRollCommand,
    D20Command,
    DisadvantageRollCommand,
    MultiRollCommand,
    RollCommand,
)
from commands.search import SearchCommandGroup
from commands.stats import StatsCommandGroup
from commands.timestamp import TimestampCommandGroup
from commands.tokengen import TokenGenCommandGroup
from context_menus.delete import DeleteContextMenu
from context_menus.reroll import RerollContextMenu
from context_menus.timestamp import RequestTimestampContextMenu
from context_menus.zip_files import ZipAttachmentsContextMenu
from logic.voice_chat import VC, Sounds


class Bot(discord.Client):
    tree: app_commands.CommandTree
    token: str
    guild_id: int | None
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

        token = os.getenv("DISCORD_BOT_TOKEN")
        if not token:
            logging.warning("Could not get bot token, is the .env file correctly configured?")
            token = ""

        self.token = token
        guild_id = os.getenv("GUILD_ID")
        self.guild_id = int(guild_id) if guild_id is not None else None
        self.voice_enabled = voice

    def register_commands(self):
        logging.info("Registering slash-commands")

        # Commands
        self.tree.add_command(DistributionCommand())
        self.tree.add_command(HelpCommand(tree=self.tree))
        self.tree.add_command(StatsCommandGroup())
        self.tree.add_command(RollCommand())
        self.tree.add_command(AdvantageRollCommand())
        self.tree.add_command(DisadvantageRollCommand())
        self.tree.add_command(D20Command())
        self.tree.add_command(MultiRollCommand())
        self.tree.add_command(TokenGenCommandGroup())
        self.tree.add_command(InitiativeCommand())
        self.tree.add_command(PlanSessionCommand())
        self.tree.add_command(PlaySoundCommand())
        self.tree.add_command(ColorCommandGroup())
        self.tree.add_command(NameGenCommand())
        self.tree.add_command(CharacterGenCommand())
        self.tree.add_command(ConfigCommand())
        self.tree.add_command(SearchCommandGroup())
        self.tree.add_command(TimestampCommandGroup())
        self.tree.add_command(HomebrewCommandGroup())
        self.tree.add_command(ProfileCommandGroup())

        # Context menus
        self.tree.add_command(DeleteContextMenu())
        self.tree.add_command(RerollContextMenu())
        self.tree.add_command(RequestTimestampContextMenu())
        self.tree.add_command(ZipAttachmentsContextMenu())

        logging.info("Registered slash-commands")

    def run_client(self):
        """Starts the bot using the token stored in .env"""
        # log_handler set to None, as a handler is already added in main.py
        super().run(self.token, log_handler=None)

    async def on_ready(self):
        """Runs automatically when the bot is online"""
        if self.user is None:
            raise RuntimeError("The bot is not associated with a user client account!")

        logging.info("Initializing")
        logging.info("Logged in as %s (ID: %d)", self.user.name, self.user.id)

        self.register_commands()
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
            logging.info("Connected to guild: %s (ID: %d)", guild.name, guild.id)
