import discord

from command import SimpleContextMenu


class DeleteContextMenu(SimpleContextMenu):
    name = "Delete message"
    help = "Deletes the bot's message, useful for cleaning up accidental searches, spoilers or general bot-clutter."

    def __init__(self):
        super().__init__()

    async def callback(self, interaction: discord.Interaction, message: discord.Message):
        self.log(interaction)
        if not interaction.client.user:
            error = "The bot is not associated with a user account!"
            await interaction.response.send_message(f"❌ {error} ❌", ephemeral=True)
            return

        if message.author.id != interaction.client.user.id:
            error = f"{interaction.client.user.name} can only delete their own messages!"
            await interaction.response.send_message(f"❌ {error} ❌", ephemeral=True)
            return

        await message.delete()
        await interaction.response.send_message("Message deleted!", ephemeral=True)
