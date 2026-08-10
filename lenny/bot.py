import logging
import os

import discord
from discord import InteractionType, app_commands
from discord.ext import tasks
from dotenv import load_dotenv

from logger import (
    log_application_command_interaction,
    log_component_interaction,
    log_modal_submit_interaction,
)
from logic.config import Config
from logic.dicecache import DiceCache
from logic.favorites import FavoritesCache
from logic.homebrew import HomebrewData
from logic.searchcache import SearchCache
from logic.voice_chat import VC, Sounds
from services.commands import CommandRegistry


class Bot(discord.Client):
    tree: app_commands.CommandTree
    token: str
    guild_id: int | None
    voice_enabled: bool
    commands: CommandRegistry

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
        self.commands = CommandRegistry(self.tree)

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

        self.commands.find_and_register()
        await self.commands.sync(self.guild_id, self.guilds)

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
        self._cache_cleaner.start()
        self._frequent_cleanup.start()

    @tasks.loop(hours=1)
    async def _cache_cleaner(self):
        logging.debug("Cleaning cache...")
        HomebrewData.clear_cache()
        DiceCache.clear_cache(max_age=900)
        Config.clear_cache(max_age=900)
        SearchCache.clear_cache(max_age=450)
        FavoritesCache.clear_cache(max_age=450)

    @tasks.loop(minutes=3)
    async def _frequent_cleanup(self):
        await VC.leave_inactive_voice_chats()

    async def on_interaction(self, interaction: discord.Interaction):
        match interaction.type:
            case InteractionType.application_command:
                log_application_command_interaction(interaction)
            case InteractionType.component:
                log_component_interaction(interaction)
            case InteractionType.modal_submit:
                log_modal_submit_interaction(interaction)
            case _:
                ...
