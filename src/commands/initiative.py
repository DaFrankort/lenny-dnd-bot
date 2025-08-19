import discord

from i18n import t
from initiative import InitiativeEmbed, InitiativeTracker
from logger import log_cmd
from voice_chat import VC, SoundType


class InitiativeCommand(discord.app_commands.Command):
    name = t("commands.initiative.name")
    description = t("commands.initiative.desc")

    initiatives: InitiativeTracker

    def __init__(self, initiatives: InitiativeTracker):
        self.initiatives = initiatives
        super().__init__(
            name=self.name,
            description=self.description,
            callback=self.callback,
        )

    async def callback(self, itr: discord.Interaction):
        log_cmd(itr)
        embed = InitiativeEmbed(itr, self.initiatives)
        await itr.response.send_message(embed=embed, view=embed.view)
        await VC.play(itr, SoundType.INITIATIVE)

        message = await itr.original_response()
        await self.initiatives.set_message(itr, message)
