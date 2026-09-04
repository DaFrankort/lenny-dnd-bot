import discord
from discord.app_commands import Range, describe

from commands.command import BaseCommand
from embeds.grouproll import GroupRollContainerView
from logic.voice_chat import VC, SoundType


class GroupRollCommand(BaseCommand):
    name = "grouproll"
    desc = "Allow your players to roll multiple d20s all at once!"
    help = "Summons an embed with buttons, so multiple people can roll at once."

    @describe(reason="The reason why everyone is rolling.")
    async def handle(self, itr: discord.Interaction, reason: Range[str, 1, 45]):
        view = GroupRollContainerView(reason=reason)
        await itr.response.send_message(view=view)
        await VC.play(itr, SoundType.LOCK, True)
