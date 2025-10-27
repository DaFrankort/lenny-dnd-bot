import discord

from logic.homebrew import DNDHomebrewObject, HomebrewData
from modals import SimpleModal


class HomebrewEmbed(discord.Embed):
    view: discord.ui.View = None

    def __init__(self, itr: discord.Interaction, entry: DNDHomebrewObject):
        subtitle = f"*{entry.select_description}*\n\n"
        if len(entry.description) < 4000 - len(subtitle) and entry.select_description:
            description = subtitle + entry.description
        else:
            description = entry.description

        super().__init__(title=entry.title, type="rich", description=description, color=discord.Color.blue())

        author = entry.get_author(itr)
        if author:
            self.set_footer(text=f"Created by {author.display_name}", icon_url=author.display_avatar.url)
        else:
            self.set_footer(text="Created by Unknown User", icon_url=itr.client.user.avatar.url)


class HomebrewEntryAddModal(SimpleModal):
    dnd_type: str
    name = discord.ui.TextInput(label="Name", placeholder="Peanut")
    subtitle = discord.ui.TextInput(
        label="Subtitle",
        placeholder="A small legume",
        required=False,
        max_length=80,
    )
    description = discord.ui.TextInput(
        label="Description",
        placeholder="A peanut is a legume that is often mistaken for a nut.",
        max_length=4000,
        style=discord.TextStyle.paragraph,
    )

    def __init__(self, dnd_type: str):
        self.dnd_type = dnd_type
        super().__init__(itr=None, title=f"Add new {dnd_type.title()}")

    async def on_submit(self, itr: discord.Interaction):
        self.log_inputs(itr)

        name = self.get_str(self.name)
        subtitle = self.get_str(self.subtitle)
        description = self.get_str(self.description)

        if not name or not description:
            await itr.response.send_message("Name and Description are required fields.", ephemeral=True)
            return

        entry = HomebrewData.get(itr).add(itr, self.dnd_type, name=name, select_description=subtitle, description=description)
        embed = HomebrewEmbed(itr, entry)
        await itr.response.send_message(content=f"Added {self.dnd_type}: ``{name}``!", embed=embed, ephemeral=True)
