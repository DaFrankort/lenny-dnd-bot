import logging
import os

import discord
from discord import InteractionType, app_commands
from discord.enums import EventStatus
from discord.ext import tasks
from dotenv import load_dotenv

from commands.average import AverageDamageCommandGroup
from commands.charactergen import CharacterGenCommand
from commands.coin import CoinCommand
from commands.color import ColorCommandGroup
from commands.config import ConfigCommand
from commands.distribution import DistributionCommand
from commands.favorites import FavoritesCommandGroup
from commands.grouproll import GroupRollCommand
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
    TableRollCommand,
)
from commands.search import SearchCommandGroup
from commands.session import SessionStatsCommandGroup
from commands.stats import StatsCommandGroup
from commands.timestamp import TimestampCommandGroup
from commands.tokengen import TokenGenCommandGroup
from context_menus.delete import DeleteContextMenu
from context_menus.favorites import AddFavoriteContextMenu
from context_menus.reroll import RerollContextMenu
from context_menus.timestamp import RequestTimestampContextMenu
from context_menus.zip_files import ZipAttachmentsContextMenu
from logger import (
    log_application_command_interaction,
    log_component_interaction,
    log_modal_submit_interaction,
)
from logic.config import CalendarTargetConfig, Config
from logic.dicecache import DiceCache
from logic.favorites import FavoritesCache
from logic.google_calendar import (
    GoogleCalendarSync,
    build_reminder_message,
    event_calendar_markers,
    is_reminder_due,
)
from logic.homebrew import HomebrewData
from logic.searchcache import SearchCache
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
        intents.guild_scheduled_events = True
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
        self._scheduled_events: dict[int, discord.ScheduledEvent] = {}

    def register_commands(self):
        logging.info("Registering slash-commands")

        # Commands
        self.tree.add_command(DistributionCommand())
        self.tree.add_command(HelpCommand(tree=self.tree))
        self.tree.add_command(StatsCommandGroup())
        self.tree.add_command(RollCommand())
        self.tree.add_command(D20Command())
        self.tree.add_command(MultiRollCommand())
        self.tree.add_command(TableRollCommand())
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
        self.tree.add_command(FavoritesCommandGroup())
        self.tree.add_command(AverageDamageCommandGroup())
        self.tree.add_command(SessionStatsCommandGroup())
        self.tree.add_command(CoinCommand())
        self.tree.add_command(GroupRollCommand())

        # Context menus
        self.tree.add_command(DeleteContextMenu())
        self.tree.add_command(AddFavoriteContextMenu())
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
        await self._load_calendar_events()
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
        if not self._calendar_reminders.is_running():
            self._calendar_reminders.start()
        if not self._calendar_reconcile.is_running():
            self._calendar_reconcile.start()

    async def _load_calendar_events(self):
        for guild in self.guilds:
            if not Config.get_for_guild(guild).config.calendar_targets:
                continue

            await self.refresh_calendar_events(guild)

    async def refresh_calendar_events(self, guild: discord.Guild):
        config = Config.get_for_guild(guild).config
        if not config.calendar_targets:
            return

        try:
            events = await guild.fetch_scheduled_events(with_counts=False)
        except discord.HTTPException:
            logging.exception("Failed to fetch scheduled events in guild %s", guild.id)
            return

        event_ids = {event.id for event in events}
        for event_id in list(config.calendar_event_ids):
            if event_id not in event_ids:
                await GoogleCalendarSync.delete_event_by_id(guild, event_id)

        for event_id, event in list(self._scheduled_events.items()):
            if event.guild is None or event.guild.id == guild.id:
                self._scheduled_events.pop(event_id)

        for event in events:
            self._scheduled_events[event.id] = event
            await GoogleCalendarSync.sync_event(event)

    async def on_scheduled_event_create(self, event: discord.ScheduledEvent):
        self._scheduled_events[event.id] = event
        await GoogleCalendarSync.sync_event(event)

    async def on_scheduled_event_update(self, before: discord.ScheduledEvent, after: discord.ScheduledEvent):
        if after.guild is None:
            self._scheduled_events.pop(after.id, None)
            return

        if after.status is EventStatus.canceled:
            self._scheduled_events.pop(after.id, None)
        else:
            self._scheduled_events[after.id] = after
        if before.start_time != after.start_time:
            config = Config.get_for_guild(after.guild)
            reminder_prefix = f"{after.id}:"
            updated_reminders = [
                key for key in config.config.calendar_sent_reminders if not key.startswith(reminder_prefix)
            ]
            if len(updated_reminders) != len(config.config.calendar_sent_reminders):
                config.config.calendar_sent_reminders = updated_reminders
                config.save()
        await GoogleCalendarSync.sync_event(after)

    async def on_scheduled_event_delete(self, event: discord.ScheduledEvent):
        self._scheduled_events.pop(event.id, None)
        await GoogleCalendarSync.delete_event(event)

    @tasks.loop(minutes=1)
    async def _calendar_reminders(self):
        now = discord.utils.utcnow()
        for event in list(self._scheduled_events.values()):
            guild = event.guild
            if guild is None:
                continue

            config_handler = Config.get_for_guild(guild)
            config = config_handler.config
            markers = event_calendar_markers(event)
            for target_name, target in config.calendar_targets.items():
                if target_name not in markers:
                    continue

                for phase, reminder_hours, at_start in (
                    ("before", target.reminder_hours, False),
                    ("start", 0, True),
                ):
                    reminder_key = f"{event.id}:{target_name}:{phase}"
                    if reminder_key in config.calendar_sent_reminders:
                        continue
                    if not is_reminder_due(event, now, reminder_hours, at_start=at_start):
                        continue

                    sent = await self._send_calendar_reminder(event, target, target_name, phase)
                    if not sent:
                        continue
                    if reminder_key not in config.calendar_sent_reminders:
                        config.calendar_sent_reminders.append(reminder_key)
                        config_handler.save()

    async def _send_calendar_reminder(
        self,
        event: discord.ScheduledEvent,
        target: CalendarTargetConfig,
        target_name: str,
        phase: str,
    ) -> bool:
        guild = event.guild
        if guild is None:
            return False

        channel = guild.get_channel(target.announcement_channel_id)
        if not isinstance(channel, discord.TextChannel):
            logging.warning(
                "Calendar reminder channel %s is unavailable for target %s in guild %s",
                target.announcement_channel_id,
                target_name,
                guild.id,
            )
            return False

        role = guild.get_role(target.reminder_role_id) if target.reminder_role_id is not None else None
        if target.reminder_role_id is not None and role is None:
            logging.warning("Calendar reminder role %s is unavailable in guild %s", target.reminder_role_id, guild.id)
            return False

        message, allowed_mentions = build_reminder_message(event, role, at_start=phase == "start")
        try:
            await channel.send(message, allowed_mentions=allowed_mentions)
        except discord.HTTPException:
            logging.exception("Failed to send %s reminder for event %s", phase, event.id)
            return False
        return True

    @tasks.loop(minutes=15)
    async def _calendar_reconcile(self):
        await self._load_calendar_events()

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
