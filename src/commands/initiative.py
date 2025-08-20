import discord

from initiative import InitiativeContainerView, InitiativeTracker
from logger import log_cmd
from voice_chat import VC, SoundType


class InitiativeCommand(discord.app_commands.Command):
    name = "initiative"
    desc = "Start tracking initiatives for combat!"
    help = "Summons an embed with buttons, to set up combat-initiatives."
    command = "/initiative"

    initiatives: InitiativeTracker

    def __init__(self, initiatives: InitiativeTracker):
        self.initiatives = initiatives
        super().__init__(
            name=self.name,
            description=self.desc,
            callback=self.callback,
        )

    async def callback(self, itr: discord.Interaction):
        log_cmd(itr)
        view = InitiativeContainerView(itr, self.initiatives)
        await itr.response.send_message(view=view)
        await VC.play(itr, SoundType.INITIATIVE)

        message = await itr.original_response()
        await self.initiatives.set_message(itr, message)
