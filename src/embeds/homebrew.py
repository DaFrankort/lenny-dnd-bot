import discord
from discord import ui
from components.items import SimpleSeparator, TitleTextDisplay
from components.paginated_view import PaginatedLayoutView
from logic.homebrew import HomebrewEntry, HomebrewData, HomebrewEntryType
from methods import MDFile
from components.modals import SimpleModal


class HomebrewEmbed(discord.Embed):
    def __init__(self, itr: discord.Interaction, entry: HomebrewEntry):
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
            icon_url = None
            if itr.client.user is not None and itr.client.user.avatar is not None:
                icon_url = itr.client.user.avatar.url
            self.set_footer(text="Created by Unknown User", icon_url=icon_url)


class HomebrewEntryAddModal(SimpleModal):
    type: HomebrewEntryType
    name = ui.TextInput["HomebrewListView"](label="Name", placeholder="Peanut")
    subtitle = ui.TextInput["HomebrewListView"](
        label="Subtitle",
        placeholder="A small legume",
        required=False,
        max_length=80,
    )
    description = ui.TextInput["HomebrewListView"](
        label="Description",
        placeholder="A peanut is a legume that is often mistaken for a nut.",
        max_length=4000,
        style=discord.TextStyle.paragraph,
    )

    def __init__(self, itr: discord.Interaction, dnd_type: HomebrewEntryType, md_file: MDFile | None):
        if md_file:
            if len(md_file.content) > 4000:
                raise ValueError(
                    "Markdown file's content exceeds exceeds character-limit!\nPlease use a file with less than 4000 characters."
                )
            self.name.default = md_file.title
            self.name.placeholder = self.format_placeholder(md_file.title)
            self.description.default = md_file.content
            self.description.placeholder = self.format_placeholder(md_file.content)
        self.type = dnd_type
        super().__init__(itr=itr, title=f"Add new {dnd_type.title()}")

    async def on_submit(self, itr: discord.Interaction):
        self.log_inputs(itr)

        name = self.get_str(self.name)
        subtitle = self.get_str(self.subtitle)
        description = self.get_str(self.description)

        if not name or not description:
            await itr.response.send_message("Name and Description are required fields.", ephemeral=True)
            return

        entry = HomebrewData.get(itr).add(itr, self.type, name=name, select_description=subtitle, description=description)
        embed = HomebrewEmbed(itr, entry)
        await itr.response.send_message(content=f"Added {self.type.value}: ``{name}``!", embed=embed, ephemeral=True)


class HomebrewEditModal(SimpleModal):
    entry: HomebrewEntry
    name = ui.TextInput["HomebrewListView"](label="Name")
    subtitle = ui.TextInput["HomebrewListView"](label="Subtitle", required=False, max_length=80)
    description = ui.TextInput["HomebrewListView"](label="Description", max_length=4000, style=discord.TextStyle.paragraph)

    def __init__(self, itr: discord.Interaction, entry: HomebrewEntry):
        self.entry = entry
        self.name.default = entry.name
        self.name.placeholder = entry.name
        self.subtitle.default = entry.select_description or ""
        self.subtitle.placeholder = entry.select_description or "Subtitle"
        self.description.default = entry.description
        self.description.placeholder = self.format_placeholder(entry.description)
        super().__init__(itr=itr, title=f"Edit {entry.entry_type.value}: {entry.name}")

    async def on_submit(self, itr: discord.Interaction):
        self.log_inputs(itr)

        name = self.get_str(self.name)
        subtitle = self.get_str(self.subtitle)
        description = self.get_str(self.description)

        if not name or not description:
            await itr.response.send_message("Name and Description are required fields.", ephemeral=True)
            return

        updated_entry = HomebrewData.get(itr).edit(itr, self.entry, name, subtitle, description)
        embed = HomebrewEmbed(itr, updated_entry)
        await itr.response.send_message(
            content=f"Edited {self.entry.entry_type.value}: ``{self.entry.name}`` => ``{name}``!", embed=embed, ephemeral=True
        )


class HomebrewListButton(ui.Button["HomebrewListView"]):
    entry: HomebrewEntry

    def __init__(self, entry: HomebrewEntry):
        self.entry = entry
        label = entry.name
        if len(label) > 80:
            label = label[:77] + "..."
        super().__init__(label=label, emoji=entry.emoji, style=discord.ButtonStyle.gray)

    async def callback(self, interaction: discord.Interaction):
        embed = HomebrewEmbed(interaction, self.entry)
        await interaction.response.send_message(embed=embed)


class HomebrewListView(PaginatedLayoutView):
    filter: HomebrewEntryType | None
    entries: list[HomebrewEntry]

    def __init__(self, itr: discord.Interaction, filter: str | None):
        self.filter = None
        label = "All Entries"
        if filter is not None:
            self.filter = HomebrewEntryType(filter)
            label = filter.title()

        self.entries = HomebrewData.get(itr).get_all(self.filter)
        if len(self.entries) < 1:
            if self.filter is None:
                raise RuntimeError("This server does not have any homebrew-content yet.")
            raise RuntimeError(f"This server does not have any homebrew {label}-content yet.")

        super().__init__()

        title = f"{len(self.entries)} Homebrew Entries ({label})"
        self.title_item = TitleTextDisplay(name=title, url=None)
        self.build()

    @property
    def entry_count(self) -> int:
        return len(self.entries)

    def get_current_options(self):
        start = self.page * self.per_page
        end = (self.page + 1) * self.per_page
        return self.entries[start:end]

    def build(self):
        self.clear_items()
        container = ui.Container["HomebrewListView"](accent_color=discord.Color.blue())

        # HEADER
        container.add_item(self.title_item)
        container.add_item(SimpleSeparator())

        # CONTENT
        options = self.get_current_options()
        for option in options:
            row = ui.ActionRow(HomebrewListButton(option))
            container.add_item(row)

        # FOOTER
        container.add_item(SimpleSeparator())
        container.add_item(self.navigation_footer())

        self.add_item(container)
