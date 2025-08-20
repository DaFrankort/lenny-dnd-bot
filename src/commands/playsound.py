import discord
from discord import app_commands
from embeds import SuccessEmbed
from i18n import t
from logger import log_cmd
from voice_chat import VC


def check_user_in_vc():
    async def predicate(itr: discord.Interaction) -> bool:
        if itr.user is None or not isinstance(itr.user, discord.Member):
            return False
        return itr.user.voice is not None and itr.user.voice.channel is not None

    return app_commands.check(predicate)


class PlaySoundCommand(app_commands.Command):
    name = t("commands.playsound.name")
    description = t("commands.playsound.desc")

    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.description,
            callback=self.callback,
        )

    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @check_user_in_vc()
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
