import discord

from app_commands import SimpleCommand
from initiative import InitiativeContainerView, InitiativeTracker
from voice_chat import VC, SoundType


class InitiativeCommand(SimpleCommand):
    name = "initiative"
    desc = "Start tracking initiatives for combat!"
    help = "Summons an embed with buttons, to set up combat-initiatives."

    initiatives: InitiativeTracker

    def __init__(self, initiatives: InitiativeTracker):
        self.initiatives = initiatives
        super().__init__()

    async def callback(self, itr: discord.Interaction):
        self.log(itr)
        view = InitiativeContainerView(itr, self.initiatives)
        await itr.response.send_message(view=view)
        await VC.play(itr, SoundType.INITIATIVE)

        message = await itr.original_response()
        await self.initiatives.set_message(itr, message)
