import logging
import subprocess
import discord

class VoiceChat:
    client: discord.VoiceClient
    ffmpeg_available: bool = False

    @staticmethod
    def check_ffmpeg():
        try:
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            logging.info("FFmpeg installed and available, using voice chat functionality.")
            VoiceChat.ffmpeg_available = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logging.warning("FFmpeg is not installed or not found in PATH, voice chat functionality will be disabled.")

    @staticmethod
    async def join(ctx: discord.Interaction):
        if ctx.user.voice:
            channel = ctx.user.voice.channel
            if ctx.guild.voice_client is None:
                VoiceChat.client = await channel.connect()
            else:
                VoiceChat.client = ctx.guild.voice_client

            logging.info(f"Joined voicechat: {VoiceChat.client.channel.name}")

    @staticmethod
    async def leave(ctx: discord.Interaction):
        VoiceChat.client = ctx.guild.voice_client
        if ctx.voice_client:
            ctx.voice_client.disconnect()
            logging.info("Left the voice channel.")

    @staticmethod
    async def play(ctx: discord.Interaction, audio_file: str):
        if not VoiceChat.ffmpeg_available:
            return

        if not ctx.guild or not ctx.user.voice:
            return # User in DMs or not in voice chat
        
        await VoiceChat.join(ctx)

        if VoiceChat.client.is_playing():
            VoiceChat.client.stop()

        try:
            VoiceChat.client.play(discord.FFmpegPCMAudio(source="./sounds/test_sound.mp3"))
        except Exception as e:
            logging.error(f"Error playing audio: {e}")
            return