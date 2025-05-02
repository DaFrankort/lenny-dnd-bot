import logging
import discord

class VoiceChat:
    client: discord.VoiceClient

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
        if not ctx.guild or not ctx.user.voice:
            return # User in DMs or not in voice chat
        
        await VoiceChat.join(ctx)

        if VoiceChat.client.is_playing():
            VoiceChat.client.stop()

        # VoiceChat.client.play(discord.FFmpegPCMAudio(source=audio_file))