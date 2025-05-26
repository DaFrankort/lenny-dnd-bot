import asyncio
from enum import Enum
import logging
from pathlib import Path
import random
import shutil
import discord

from dice import DiceExpression
from initiative import Initiative


class SoundType(Enum):
    ROLL = "dice/roll"
    NAT_20 = "dice/nat_20"
    NAT_1 = "dice/nat_1"
    DIRTY_20 = "dice/dirty_20"
    ATTACK = "combat/attack"
    DAMAGE = "combat/damage"
    FIRE = "combat/fire"


class VC:
    clients: dict[int, discord.VoiceClient] = {}
    ffmpeg_available: bool = False

    @staticmethod
    def check_ffmpeg():
        """Check if FFmpeg is installed and available in PATH. If not installed, disable voice chat functionality."""
        if shutil.which("ffmpeg") is None:
            logging.warning(
                "FFmpeg not installed or found in PATH, voice chat features are disabled."
            )
            VC.ffmpeg_available = False
            return

        logging.info("FFmpeg available, voice chat features are enabled.")
        VC.ffmpeg_available = True

    @staticmethod
    async def join(itr: discord.Interaction):
        """Join the voice channel of the user who invoked the command."""
        if not VC.ffmpeg_available:
            return

        if not itr.guild or not itr.user.voice:
            return  # User in DMs or not in voice chat

        guild_id = itr.guild_id
        voice_channel = itr.user.voice.channel

        old_client = VC.clients.get(guild_id)
        if old_client:
            if old_client.channel.id == voice_channel.id:
                return
            await VC.leave(guild_id)  # Need to leave current channel to switch.

        client = await voice_channel.connect()
        VC.clients[guild_id] = client
        logging.info(
            f"Joined voice channel '{client.channel.name}' in '{client.guild.name}'"
        )
        asyncio.create_task(VC.monitor_vc(guild_id))

    @staticmethod
    async def leave(guild_id: int):
        client = VC.clients.get(guild_id)
        if client:
            logging.info(
                f"Left voice channel '{client.channel.name}' in '{client.guild.name}'"
            )
            await client.disconnect()
            del VC.clients[guild_id]

    @staticmethod
    async def play(itr: discord.Interaction, sound_type: SoundType):
        """Play an audio file in the voice channel."""
        if not itr.guild or not itr.user.voice:
            return  # User in DMs or not in voice chat

        await VC.join(itr)

        client = VC.clients.get(itr.guild_id)
        if not client:
            return

        retries = 0
        while client.is_playing():
            # We queue sounds for 5 seconds, to prevent abrubt sound cuts
            if retries >= 50:
                client.stop()
                break
            await asyncio.sleep(0.1)
            retries += 1

        sound = Sounds.get(sound_type)
        if sound:
            client.play(sound)

    @staticmethod
    async def play_dice_roll(
        itr: discord.Interaction, expression: DiceExpression, reason: str = None
    ):
        roll = expression.roll
        sound_type = SoundType.ROLL

        reason = "" if not reason else reason.lower().strip()
        match reason:
            case "attack":
                sound_type = SoundType.ATTACK
            case "damage":
                sound_type = SoundType.DAMAGE
            case "fire":
                sound_type = SoundType.FIRE

        if roll.is_natural_twenty:
            sound_type = SoundType.NAT_20
        elif roll.is_natural_one:
            sound_type = SoundType.NAT_1
        elif roll.is_dirty_twenty:
            sound_type = SoundType.DIRTY_20

        await VC.play(itr, sound_type)

    @staticmethod
    async def play_initiative_roll(
        itr: discord.Interaction, initiative: Initiative
    ):
        sound_type = SoundType.ROLL

        if initiative.d20 == 20:
            sound_type = SoundType.NAT_20
        elif initiative.d20 == 1:
            sound_type = SoundType.NAT_1

        await VC.play(itr, sound_type)

    @staticmethod
    async def monitor_vc(guild_id: int):
        """Periodically checks if the bot is alone in a voice channel and disconnects if so."""
        while True:
            client = VC.clients.get(guild_id)
            if not client:
                break

            channel = client.channel
            members = channel.members if channel else []
            non_bot_members = [m for m in members if not m.bot]

            if not non_bot_members:
                logging.info("Bot is alone in voice channel, disconnecting.")
                await VC.leave(guild_id)
                break

            await asyncio.sleep(60)


class Sounds:
    BASE_PATH = Path("./sounds/")

    @staticmethod
    def _get_options(sound_type: SoundType) -> str:
        """Get the FFmpeg options for the sound type."""

        def option(volume: float = 0.5, speed_deviation: float = 0) -> str:
            speed_max = min(1 + speed_deviation, 2)
            speed_min = max(1 - speed_deviation, 0.1)
            speed = round(random.uniform(speed_min, speed_max), 2)

            filters = [
                "dynaudnorm",  # Always normalize first, for stable volumes
                f"volume={volume}",
                f"atempo={speed}",
            ]

            return f"-filter:a '{','.join(filters)}'"

        options_map = {
            SoundType.ROLL: option(volume=0.3, speed_deviation=0.3),
            SoundType.ATTACK: option(speed_deviation=0.4),
            SoundType.DAMAGE: option(speed_deviation=0.5),
            SoundType.FIRE: option(speed_deviation=0.3),
            # Add sound types and specific options here
        }

        return options_map.get(sound_type, option())

    @staticmethod
    def get(sound_type: SoundType) -> discord.FFmpegPCMAudio:
        """Get a random sound file for the given sound type."""
        folder = Sounds.BASE_PATH / sound_type.value
        if not folder.exists() or not folder.is_dir():
            folder.mkdir(parents=True, exist_ok=True)

        supported_extensions = ["*.mp3", "*.ogg", "*.wav"]
        sound_files = []
        for ext in supported_extensions:
            sound_files.extend(folder.glob(ext))

        if not sound_files:
            logging.warning(f"No .mp3 files found in {folder}.")
            return None

        src = str(random.choice(sound_files))
        options = Sounds._get_options(sound_type)
        return discord.FFmpegPCMAudio(source=src, options=options)

    @classmethod
    def init_folders(cls):
        for sound_type in SoundType:
            folder = cls.BASE_PATH / sound_type.value
            folder.mkdir(parents=True, exist_ok=True)
