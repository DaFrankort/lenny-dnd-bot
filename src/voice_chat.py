import asyncio
from enum import Enum
import logging
from pathlib import Path
import random
import subprocess
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
        try:
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            logging.info("FFmpeg installed and available, using voice chat functionality.")
            VC.ffmpeg_available = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logging.warning("FFmpeg is not installed or not found in PATH, voice chat functionality will be disabled.")
            VC.ffmpeg_available = False

    @staticmethod
    async def join(itr: discord.Interaction):
        """Join the voice channel of the user who invoked the command."""
        if not VC.ffmpeg_available:
            return

        if not itr.user.voice:
            return  # User not in voice chat

        if VC.client:
            if VC.client.channel.id == itr.user.voice.channel.id:
                return  # Already in the same voice channel
            await VC.leave()

        VC.client = await itr.user.voice.channel.connect()
        logging.info(f"Joined voice channel: {VC.client.channel.name} (ID: {VC.client.channel.id})")

    @staticmethod
    async def leave():
        """Leave the voice channel."""
        if VC.client:
            logging.info(f"Left voice channel: {VC.client.channel.name} (ID: {VC.client.channel.id})")
            await VC.client.disconnect()
            VC.client = None

    @staticmethod
    async def play(itr: discord.Interaction, sound_type: SoundType):
        """Play an audio file in the voice channel."""
        if not VC.ffmpeg_available:
            return

        if not itr.guild or not itr.user.voice:
            return  # User in DMs or not in voice chat

        await VC.join(itr)

        retries = 0
        while VC.client.is_playing():
            if retries >= 20:  # 10s
                VC.client.stop()  # Stop playback, makes bot not play sounds for long periods of time
                break
            await asyncio.sleep(0.5)
            retries += 1

        try:
            VC.client.play(Sound.get(sound_type))
        except Exception as e:
            logging.error(f"Error playing audio: {e}")
            VC.check_ffmpeg()

    @staticmethod
    async def play_dice_roll(itr: discord.Interaction, expression: DiceExpression):
        sound_type = SoundType.ROLL
        if expression.roll.is_natural_twenty:
            sound_type = SoundType.NAT_20

        elif expression.roll.is_natural_one:
            sound_type = SoundType.NAT_1

        elif expression.roll.is_dirty_twenty:
            sound_type = SoundType.DIRTY_20

        await VC.play(itr, sound_type)


class Sound:
    BASE_PATH = Path("./sounds/")

    @staticmethod
    def get(sound_type: SoundType) -> discord.FFmpegPCMAudio:
        """Get the path to the sound file based on the sound type."""
        folder = Sound.BASE_PATH / sound_type.value
        if not folder.exists() or not folder.is_dir():
            folder.mkdir(parents=True, exist_ok=True)

        sound_files = list(folder.glob("*.mp3"))
        if not sound_files:
            logging.warning(f"No sound files found in {folder}.")
            return None

        src = str(random.choice(sound_files))

        def option(volume: float = 0.5) -> str:
            return f"-filter:a 'volume={volume}'"

        options = {
            SoundType.ROLL: option(),
            SoundType.NAT_20: option(),
            SoundType.NAT_1: option(),
            SoundType.DIRTY_20: option()
        }.get(sound_type, option())

        return discord.FFmpegPCMAudio(source=src, options=options)
