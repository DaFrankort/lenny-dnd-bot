import asyncio
from enum import Enum
import logging
from pathlib import Path
import random
import shutil
import discord

from dice import DiceExpression


class SoundType(Enum):
    ROLL = "roll"
    NAT_20 = "nat_20"
    NAT_1 = "nat_1"
    DIRTY_20 = "dirty_20"


class VC:
    client: discord.VoiceClient = None
    ffmpeg_available: bool = False

    @staticmethod
    def check_ffmpeg():
        """Check if FFmpeg is installed and available in PATH. If not installed, disable voice chat functionality."""
        if shutil.which("ffmpeg") is None:
            logging.warning("FFmpeg not installed or found in PATH, voice chat features are disabled.")
            VC.ffmpeg_available = False
            return

        logging.info("FFmpeg available, voice chat features are enabled.")
        VC.ffmpeg_available = True

    @staticmethod
    async def join(itr: discord.Interaction):
        """Join the voice channel of the user who invoked the command."""
        if not VC.ffmpeg_available:
            return

        if VC.client:
            if VC.client.channel.id == itr.user.voice.channel.id:
                return
            await VC.leave()  # Need to leave current channel to switch.

        VC.client = await itr.user.voice.channel.connect()
        logging.info(
            f"Joined voice channel: {VC.client.channel.name} (ID: {VC.client.channel.id})"
        )

    @staticmethod
    async def leave():
        """Leave the voice channel."""
        if VC.client:
            logging.info(
                f"Left voice channel: {VC.client.channel.name} (ID: {VC.client.channel.id})"
            )
            await VC.client.disconnect()
            VC.client = None

    @staticmethod
    async def play(itr: discord.Interaction, sound_type: SoundType):
        """Play an audio file in the voice channel."""
        if not itr.guild or not itr.user.voice:
            return  # User in DMs or not in voice chat

        await VC.join(itr)

        if not VC.client:
            return

        retries = 0
        while VC.client.is_playing():
            # We queue sounds for 5 seconds, to prevent abrubt sound cuts
            if retries >= 50:
                VC.client.stop()
                break
            await asyncio.sleep(0.1)
            retries += 1

        sound = Sound.get(sound_type)
        if sound:
            VC.client.play(sound)

    @staticmethod
    async def play_dice_roll(itr: discord.Interaction, expression: DiceExpression):
        roll = expression.roll
        sound_type = SoundType.ROLL

        if roll.is_natural_twenty:
            sound_type = SoundType.NAT_20
        elif roll.is_natural_one:
            sound_type = SoundType.NAT_1
        elif roll.is_dirty_twenty:
            sound_type = SoundType.DIRTY_20

        await VC.play(itr, sound_type)


class Sound:
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
                f"atempo={speed}"
            ]

            return f"-filter:a '{','.join(filters)}'"

        options_map = {
            SoundType.ROLL: option(volume=0.4, speed_deviation=0.3)
            # Add sound types and specific options here
        }

        return options_map.get(sound_type, option())

    @staticmethod
    def get(sound_type: SoundType) -> discord.FFmpegPCMAudio:
        """Get a random sound file for the given sound type."""
        folder = Sound.BASE_PATH / sound_type.value
        if not folder.exists() or not folder.is_dir():
            folder.mkdir(parents=True, exist_ok=True)

        sound_files = list(folder.glob("*.mp3"))
        if not sound_files:
            logging.warning(f"No .mp3 files found in {folder}.")
            return None

        src = str(random.choice(sound_files))
        options = Sound._get_options(sound_type)
        return discord.FFmpegPCMAudio(source=src, options=options)
