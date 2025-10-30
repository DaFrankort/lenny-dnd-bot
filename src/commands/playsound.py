import discord

from command import SimpleCommand
from embed import SimpleEmbed
from logic.voice_chat import VC


class PlaySoundCommand(SimpleCommand):
    name = "playsound"
    desc = "Play a sound effect from a file in voice chat!"
    help = "Allows users to play sound effects from files in voice chat without requiring any soundboard setup."

    async def callback(self, itr: discord.Interaction, sound: discord.Attachment):
        self.log(itr)
        await VC.play_attachment(itr, sound)
        embed = SimpleEmbed(
            title="Playing sound!",
            description=f"▶️ Playing ``{sound.filename}`` in {itr.user.voice.channel.mention}!",
        )
        await itr.response.send_message(embed=embed, ephemeral=True)
