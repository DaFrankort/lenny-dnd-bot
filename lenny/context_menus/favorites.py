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

    def get_container_title(self, container: discord.components.Container) -> str:
        title = None
        for child in container.children:  # type: ignore
            if isinstance(child, discord.components.TextDisplay):
                title = child.content
            elif isinstance(child, discord.components.SectionComponent):
                if not child.children[0]:
                    continue
                # Our formatting always has the first TextDisplay as the title.
                title = child.children[0].content
            else:
                continue

            if not title.startswith("###"):
                continue
            title = title.replace("###", "").strip()

            if "[" in title and "](" in title:
                # Remove URL formatting [name](url) => name
                title = title.rsplit("](")[0].replace("[", "").strip()
            break

        if not title:
            raise ValueError("Could not detect a D&D entry in this message!")
        return title

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

        name, source = None, None
        if message.embeds or len(message.embeds) != 0:
            title = self.get_embed_title(message)
            name, source = self._split_name_and_source(title)

        elif (
            message.components
            or len(message.components) != 0
            and isinstance(message.components[0], discord.components.Container)
        ):
            title = self.get_container_title(message.components[0])  # type: ignore
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
