import io
import zipfile

import discord

from commands.command import SimpleContextMenu


class ZipAttachmentsContextMenu(SimpleContextMenu):
    name = "Zip message files"
    help = "Packs all attachments from a message into one ZIP file, making it faster to download many files."

    def __init__(self):
        super().__init__()

    async def callback(self, interaction: discord.Interaction, message: discord.Message):
        self.log(interaction)
        if not interaction.client.user:
            error = "The bot is not associated with a user account!"
            await interaction.response.send_message(f"❌ {error} ❌", ephemeral=True)
            return

        if not message.attachments:
            await interaction.response.send_message("❌ This message has no attachments! ❌", ephemeral=True)
            return

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for attachment in message.attachments:
                file_bytes = await attachment.read()
                zip_file.writestr(attachment.filename, file_bytes)

        zip_buffer.seek(0)
        zip_filename = f"{message.id}_attachments.zip"
        file = discord.File(fp=zip_buffer, filename=zip_filename)
        await interaction.response.send_message(
            f"📦 Zipped {len(message.attachments)} attachment(s):", file=file, ephemeral=True
        )
