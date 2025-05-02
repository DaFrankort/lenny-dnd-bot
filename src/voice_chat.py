import logging
import subprocess
import time
import discord

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
    async def play(ctx: discord.Interaction, audio_file: str):
        """Play an audio file in the voice channel."""
        if not VC.ffmpeg_available:
            return

        if not ctx.guild or not ctx.user.voice:
            return # User in DMs or not in voice chat
        
        await VC.join(ctx)

        retries = 0
        while VC.client.is_playing():
            if retries >= 15:
                VC.client.stop()  # Stop playback to prevent infinite loop
                break
            time.sleep(1)
            retries += 1

        try:
            VC.client.play(discord.FFmpegPCMAudio(source="./sounds/test_sound.mp3", options="-filter:a \"volume=0.1\""))
        except Exception as e:
            logging.error(f"Error playing audio: {e}")
            VC.check_ffmpeg()