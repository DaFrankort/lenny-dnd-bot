import discord

from i18n import t
from logger import log_cmd


class DeleteContextMenu(discord.app_commands.ContextMenu):
    name = t("contextmenu.delete.name")

    def __init__(self):
        super().__init__(
            name=self.name,
            callback=self.callback,
        )

    async def callback(self, itr: discord.Interaction, message: discord.Message):
        log_cmd(itr)
        if message.author.id != itr.client.user.id:
            await itr.response.send_message(
                f"❌ {itr.client.user.name} can only delete their own messages ❌",
                ephemeral=True,
            )
            return

        await message.delete()
        await itr.response.send_message("Message deleted!", ephemeral=True)
