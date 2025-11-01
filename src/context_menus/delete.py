import discord

from command import SimpleContextMenu


class DeleteContextMenu(SimpleContextMenu):
    name = "Delete message"

    def __init__(self):
        super().__init__()

    async def callback(self, itr: discord.Interaction, message: discord.Message):  # pyright: ignore
        self.log(itr)
        if not itr.client.user:
            error = "The bot is not associated with a user account!"
            await itr.response.send_message(f"❌ {error} ❌", ephemeral=True)
            return

        if message.author.id != itr.client.user.id:
            error = f"{itr.client.user.name} can only delete their own messages!"
            await itr.response.send_message(f"❌ {error} ❌", ephemeral=True)
            return

        await message.delete()
        await itr.response.send_message("Message deleted!", ephemeral=True)
