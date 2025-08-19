import discord

from embeds import SuccessEmbed
from i18n import t
from logger import log_cmd
from voice_chat import VC


class PlaySoundCommand(discord.app_commands.Command):
    name = t("commands.playsound.name")
    description = t("commands.playsound.desc")

    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.description,
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
