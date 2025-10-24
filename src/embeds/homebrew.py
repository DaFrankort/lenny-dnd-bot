import discord
from discord import ui
from logic.dnd.abstract import DNDHomebrewObject
from src.modals import SimpleModal


class HomebrewEmbed(discord.Embed):
    def __init__(self, itr: discord.Interaction, entry: DNDHomebrewObject):
        subtitle = f"*{entry.select_description}*\n\n"
        if len(entry.description) < 4000 - len(subtitle):
            description = subtitle + entry.description
        else:
            description = entry.description

        super().__init__(title=entry.title, type="rich", description=description, color=discord.Color.blue())

        author = entry.get_author(itr)
        if author:
            self.set_author(name=f"Created by {author.display_name}", icon_url=author.display_avatar.url)
        else:
            self.set_author(name="Created by Unknown User", icon_url=itr.client.user.avatar.url)


class HomebrewEntryAddModal(SimpleModal):
    entry_type: str
    name = ui.TextInput(label="Name", placeholder="Peanut")
    subtitle = ui.TextInput(
        label="Subtitle (Optional)",
        placeholder="A small legume",
        required=False,
        max_length=80,
    )
    description = ui.TextInput(
        label="Description",
        placeholder="A peanut is a legume that is often mistaken for a nut. It is known for its rich flavor and versatility in culinary uses.",
        max_length=4000,
    )

    def __init__(self, entry_type: str):
        self.entry_type = entry_type
        super().__init__(title=f"Add New {entry_type}", custom_id=f"add_homebrew_{entry_type.lower()}")

    async def on_submit(self, itr: discord.Interaction):
        self.log_inputs(itr)

        name = self.get_str(self.name)
        subtitle = self.get_str(self.subtitle)
        description = self.get_str(self.description)

        if not name or not description:
            await itr.response.send_message("Name and Description are required fields.", ephemeral=True)
            return

        # TODO ADD SAVE LOGIC HERE
        entry = DNDHomebrewObject(
            object_type=self.entry_type, name=name, select_description=subtitle, description=description, author_id=itr.user.id
        )
        embed = HomebrewEmbed(itr, entry)
        await itr.response.send_message(content=f"New {self.entry_type} '{entry.name}' added!", embed=embed, ephemeral=True)
