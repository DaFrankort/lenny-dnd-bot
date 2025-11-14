import discord
from discord.app_commands import describe

from commands.command import SimpleCommand
from embeds.embed import SimpleEmbed
from logic.voice_chat import VC


class PlaySoundCommand(SimpleCommand):
    name = "playsound"
    desc = "Play a sound effect from a file in voice chat!"
    help = "Allows users to play sound effects from files in voice chat without requiring any soundboard setup."

    def __init__(self):
        super().__init__()
        self.guild_only = True

    @describe(sound="The sound file you want to play in voice-chat.")
    async def handle(self, itr: discord.Interaction, sound: discord.Attachment):
        self.log(itr)
        await VC.play_attachment(itr, sound)

        mention: str = itr.user.voice.channel.mention  # type: ignore At this point, VC.play_attachment should have done all the proper checks
        embed = SimpleEmbed(
            title="Playing sound!",
            description=f"▶️ Playing ``{sound.filename}`` in {mention}!",
        )
        await itr.response.send_message(embed=embed, ephemeral=True)
