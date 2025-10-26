import discord
from discord import ui
from logic.dnd.abstract import DNDHomebrewObject, DNDObjectList
from logic.dnd.data import Data
from modals import SimpleModal


class HomebrewEmbed(discord.Embed):
    file: discord.File = None
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
    name = ui.TextInput(label="Name", placeholder="Peanut")
    subtitle = ui.TextInput(
        label="Subtitle (Optional)",
        placeholder="A small legume",
        required=False,
        max_length=80,
    )
    description = ui.TextInput(
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

        target_list: DNDObjectList = None
        for list in Data:
            if list.object_type == self.dnd_type:
                target_list = list
                break

        entry: DNDHomebrewObject = target_list.add_homebrew_entry(itr, name, subtitle, description)
        embed = HomebrewEmbed(itr, entry)
        await itr.response.send_message(content=f"Added {self.dnd_type}: ``{entry.name}``!", embed=embed, ephemeral=True)
