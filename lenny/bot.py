from datetime import datetime, time
import logging
import os

import discord
from discord import app_commands
from discord.ext import tasks
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
from commands.roll import (
    D20Command,
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
from logic.config import Config
from logic.dicecache import DiceCache
from logic.homebrew import HomebrewData
from logic.searchcache import SearchCache
from logic.voice_chat import VC, Sounds
from methods import BotDateEvent


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

        await self._set_status()
        logging.info("Finished initialization")
        self._cache_cleaner.start()
        self._set_status.start()

    async def _attempt_sync_guild(self):
        guild = discord.utils.get(self.guilds, id=self.guild_id)
        if guild is None:
            logging.warning("Could not find guild, check .env for GUILD_ID")
        else:
            await self.tree.sync(guild=guild)
            logging.info("Connected to guild: %s (ID: %d)", guild.name, guild.id)

    @tasks.loop(hours=1)
    async def _cache_cleaner(self):
        logging.debug("Cleaning cache...")
        HomebrewData.clear_cache()
        DiceCache.clear_cache(max_age=900)
        Config.clear_cache(max_age=900)
        SearchCache.clear_cache(max_age=450)

    @tasks.loop(time=time(hour=0, minute=0, second=0))
    async def _set_status(self):
        if not self.user:
            return

        events = [
            BotDateEvent(
                name="Birthday",
                status_message=f"I've turned {datetime.now().year - 2025} today!",
                avatar_img="birthday.jpg",
                start=(1, 21),
            ),
            BotDateEvent(
                name="Christmas", status_message="Happy holidays! I hope you have Frost resistance!", avatar_img="xmas.jpg", start=(12, 1), end=(12, 26)
            ),
            BotDateEvent(
                name="New years",
                status_message=f"I hope you have a wonderful {datetime.now().year}!",
                avatar_img="default.png",
                start=(1, 1),
            ),
        ]

        status_message = "Rolling d20s!"
        # avatar_path = r"./assets/images/profile_pictures/default.webp"
        for event in events:
            if event.is_active():
                logging.info("Event detected: %s", event.name)
                status_message = event.status_message
                # avatar_path = event.avatar_path

        await self.change_presence(
            activity=discord.CustomActivity(name=status_message),
            status=discord.Status.online,
        )

        # with open(avatar_path, "rb") as f:
        #     avatar_bytes = f.read()
        # await self.user.edit(avatar=avatar_bytes)
