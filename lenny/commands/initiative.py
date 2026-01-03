import discord

from commands.command import BaseCommand
from embeds.initiative import InitiativeContainerView
from logic.initiative import Initiatives
from logic.voice_chat import VC, SoundType


class InitiativeCommand(BaseCommand):
    name = "initiative"
    desc = "Start tracking initiatives for combat!"
    help = "Summons an embed with buttons, to set up combat-initiatives."

    async def handle(self, itr: discord.Interaction):
        self.log(itr)
        view = InitiativeContainerView(itr)
        await itr.response.send_message(view=view)
        await VC.play(itr, SoundType.INITIATIVE)

        message = await itr.original_response()
        await Initiatives.set_message(itr, message)
