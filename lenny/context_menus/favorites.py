import discord

from context_menus.context_menu import BaseContextMenu
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

    def _split_name_and_source(self, title: str) -> tuple[str, str]:
        name, source = title.rsplit("(", 1)
        name = name.strip()
        source = source.replace(")", "").strip()
        return name, source

    async def handle(self, interaction: discord.Interaction, message: discord.Message):
        if not interaction.client.user:
            raise RuntimeError("The bot is not associated with a user account!")

        if message.author.id != interaction.client.user.id:
            raise PermissionError(f"Favorites only works on messages from {interaction.client.user.mention}!")

        name = None
        source = None
        if message.embeds or len(message.embeds) != 0:
            name, source = self._split_name_and_source(self.get_embed_title(message))
            name = name.strip()
            source = source.replace(")", "").strip()

        elif message.components or len(message.components) != 0 and isinstance(message.components[0], discord.ui.Container):
            container = message.components[0]
            for child in container.children:  # type: ignore
                if not isinstance(child, discord.components.TextDisplay):
                    continue

                title = child.content
                print(title)
                if not title.startswith("###"):
                    continue
                title = child.content.replace("###", "")

                if "[" in title and "](" in title:
                    # Remove URL formatting
                    title = title.rsplit("](")[0].replace("[", "").strip()
                    print(title)
                name, source = self._split_name_and_source(title)

        if name is None or source is None:
            raise ValueError("Adding to favorites doesn't work on this message type!")

        entries = Data.search(name, set([source]), 95).get_all()
        for entry in entries:
            if entry.name == name and entry.source == source:
                FavoritesCache.get(interaction).store(entry)
                await interaction.response.send_message(embed=FavoriteAddedEmbed(entry), ephemeral=True)
                return
        raise KeyError(f"Could not find entry by the name of ``{name}``")
