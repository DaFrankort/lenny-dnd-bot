import discord

from logic.app_commands import SimpleCommand
from embed import SuccessEmbed
from logic.voice_chat import VC


class PlaySoundCommand(SimpleCommand):
    name = "playsound"
    desc = "Play a sound effect from a file in voice chat!"
    help = "Allows users to play sound effects from files in voice chat without requiring any soundboard setup."

    async def callback(self, itr: discord.Interaction, sound: discord.Attachment):
        self.log(itr)
        success, description = await VC.play_attachment(itr, sound)
        embed = SuccessEmbed(
            title_success="Playing sound!",
            title_fail=f"Failed to play {sound.filename}...",
            description=description,
            success=success,
        )
        await itr.response.send_message(embed=embed, ephemeral=True)
