import asyncio
import discord
from commands.command import SimpleCommand


class LateCommand(SimpleCommand):
    name = "late"
    desc = "Pester a late player until they join voice chat!"
    help = "Will ping a player until they join voice chat, please use with care."

    async def handle(self, itr: discord.Interaction, user: discord.Member):
        self.log(itr)

        if not itr.channel or isinstance(itr.channel, discord.ForumChannel) or isinstance(itr.channel, discord.CategoryChannel):
            raise RuntimeError("Unable to pester user in a channel of this type!")

        if itr.user.bot:
            raise RuntimeError("User may not be a bot!")

        await itr.response.defer()
        message = None
        while not user.voice:
            if not itr.user.voice or not isinstance(itr.user.voice, discord.VoiceState):  # type: ignore
                raise RuntimeError("You must be in a voice-channel to use this command!")

            if message:
                await message.delete()

            message = await itr.channel.send(content=f"You're late, {user.mention}! Please join {itr.user.voice.channel.mention}!")  # type: ignore
            await asyncio.sleep(5)

        if message:
            await message.delete()
        await itr.followup.send(f"Pestering complete! {user.mention} is now in voice-chat!")
