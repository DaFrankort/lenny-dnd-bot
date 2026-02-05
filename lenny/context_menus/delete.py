import discord

from context_menus.context_menu import BaseContextMenu


class DeleteContextMenu(BaseContextMenu):
    name = "❌ Delete message"
    help = "Deletes the bot's message, useful for cleaning up accidental searches, spoilers or general bot-clutter."

    async def handle(self, interaction: discord.Interaction, message: discord.Message):
        if not interaction.client.user:
            raise RuntimeError("The bot is not associated with a user account!")

        if message.author.id != interaction.client.user.id:
            raise PermissionError(f"{interaction.client.user.name} can only delete their own messages!")

        await message.delete()
        await interaction.response.send_message("Message deleted!", ephemeral=True)
