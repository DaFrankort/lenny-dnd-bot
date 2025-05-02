import logging
import subprocess
import discord

class VC:
    client: discord.VoiceClient
    ffmpeg_available: bool = False

    @staticmethod
    def check_ffmpeg():
        try:
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            logging.info("FFmpeg installed and available, using voice chat functionality.")
            VC.ffmpeg_available = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logging.warning("FFmpeg is not installed or not found in PATH, voice chat functionality will be disabled.")

    @staticmethod
    async def join(ctx: discord.Interaction):
        if ctx.user.voice:
            channel = ctx.user.voice.channel
            if ctx.guild.voice_client is None:
                VC.client = await channel.connect()
            else:
                VC.client = ctx.guild.voice_client

            logging.info(f"Joined VC: {VC.client.channel.name}")

    @staticmethod
    async def leave(ctx: discord.Interaction):
        VC.client = ctx.guild.voice_client
        if ctx.voice_client:
            ctx.voice_client.disconnect()
            logging.info("Left the voice channel.")

    @staticmethod
    async def play(ctx: discord.Interaction, audio_file: str):
        if not VC.ffmpeg_available:
            return

        if not ctx.guild or not ctx.user.voice:
            return # User in DMs or not in voice chat
        
        await VC.join(ctx)

        if VC.client.is_playing():
            VC.client.stop()

        try:
            VC.client.play(discord.FFmpegPCMAudio(source="./sounds/test_sound.mp3"))
        except Exception as e:
            logging.error(f"Error playing audio: {e}")
            return