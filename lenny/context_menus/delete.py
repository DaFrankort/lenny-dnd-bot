import discord

from commands.command import BaseContextMenu


class DeleteContextMenu(BaseContextMenu):
    name = "❌ Delete message"
    help = "Deletes the bot's message, useful for cleaning up accidental searches, spoilers or general bot-clutter."

    async def handle(self, interaction: discord.Interaction, message: discord.Message):
        self.log(interaction)
        if not interaction.client.user:
            raise ValueError("The bot is not associated with a user account!")

        if message.author.id != interaction.client.user.id:
            raise PermissionError(f"{interaction.client.user.name} can only delete their own messages!")

        await message.delete()
        await interaction.response.send_message("Message deleted!", ephemeral=True)
