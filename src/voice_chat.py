import asyncio
from enum import Enum
import logging
from pathlib import Path
import random
import subprocess
import discord


class SoundType(Enum):
    ROLL = "roll"
    NAT_20 = "nat_20"
    NAT_1 = "nat_1"
    DIRTY_20 = "dirty_20"


class VC:
    client: discord.VoiceClient
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

    @staticmethod
    async def join(ctx: discord.Interaction):
        """Join the voice channel of the user who invoked the command."""
        if ctx.user.voice:
            channel = ctx.user.voice.channel
            if ctx.guild.voice_client is None:
                VC.client = await channel.connect()
            else:
                VC.client = ctx.guild.voice_client

            logging.info(f"Joined VC: {VC.client.channel.name}")

    @staticmethod
    async def leave():
        """Leave the voice channel."""
        if VC.client:
            VC.client.disconnect()
            logging.info("Left the voice channel.")
        VC.client = None

    @staticmethod
    async def play(ctx: discord.Interaction, sound_type: SoundType):
        """Play an audio file in the voice channel."""
        if not VC.ffmpeg_available:
            return

        if not ctx.guild or not ctx.user.voice:
            return  # User in DMs or not in voice chat

        await VC.join(ctx)

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
        options = {
            SoundType.ROLL: "-filter:a 'volume=0.1'",
            SoundType.NAT_20: "-filter:a 'volume=0.5'",
            SoundType.NAT_1: "-filter:a 'volume=0.5'",
            SoundType.DIRTY_20: "-filter:a 'volume=0.5'"
        }.get(sound_type, "-filter:a 'volume=0.1'")

        return discord.FFmpegPCMAudio(source=src, options=options)
