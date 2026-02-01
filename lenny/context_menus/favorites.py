import discord

from commands.command import BaseContextMenu
from embeds.favorites import FavoriteAddedEmbed
from logic.dnd.data import Data
from logic.favorites import FavoritesCache


class AddFavoriteContextMenu(BaseContextMenu):
    name = "⭐ Add to Favorites"
    help = "Adds an entry to favorites, if the message contains a 5e.tools entry."

    def get_embed_title(self, message: discord.Message) -> str:
        embed = message.embeds[0]
        if embed and embed.title:
            return embed.title

        raise ValueError("Could not detect a D&D entry in this message!")

    async def handle(self, interaction: discord.Interaction, message: discord.Message):
        self.log(interaction)
        if not interaction.client.user:
            raise ValueError("The bot is not associated with a user account!")

        if message.author.id != interaction.client.user.id:
            raise ValueError(f"Favorites only works on messages from {interaction.client.user.mention}!")

        if not message.embeds or len(message.embeds) == 0:
            raise ValueError("Adding to favorites doesn't work on this message type!")

        name, source = self.get_embed_title(message).rsplit("(", 1)
        name = name.strip()
        source = source.replace(")", "").strip()

        entries = Data.search(name, set([source]), 95).get_all()
        for entry in entries:
            if entry.name == name and entry.source == source:
                FavoritesCache.get(interaction).store(entry)
                await interaction.response.send_message(embed=FavoriteAddedEmbed(entry), ephemeral=True)
                return

        raise ValueError(f"Could not find entry by the name of ``{name}``")
