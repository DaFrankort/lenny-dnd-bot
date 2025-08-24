import discord

from logic.app_commands import SimpleContextMenu


class DeleteContextMenu(SimpleContextMenu):
    name = "Delete message"

    def __init__(self):
        super().__init__()

    async def callback(self, itr: discord.Interaction, message: discord.Message):
        self.log(itr)
        if message.author.id != itr.client.user.id:
            await itr.response.send_message(
                f"❌ {itr.client.user.name} can only delete their own messages ❌",
                ephemeral=True,
            )
            return

        await message.delete()
        await itr.response.send_message("Message deleted!", ephemeral=True)
