import discord

from embeds import SuccessEmbed
from logger import log_cmd
from voice_chat import VC


class PlaySoundCommand(discord.app_commands.Command):
    name = "playsound"
    desc = "Play a sound effect from a file in voice chat!"
    help = "Allows users to play sound effects from files in voice chat without requiring any soundboard setup."
    command = "/playsound <audio-file>"

    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.desc,
            callback=self.callback,
        )

    async def callback(self, itr: discord.Interaction, sound: discord.Attachment):
        log_cmd(itr)
        success, description = await VC.play_attachment(itr, sound)
        embed = SuccessEmbed(
            title_success="Playing sound!",
            title_fail=f"Failed to play {sound.filename}...",
            description=description,
            success=success,
        )
        await itr.response.send_message(embed=embed, ephemeral=True)
