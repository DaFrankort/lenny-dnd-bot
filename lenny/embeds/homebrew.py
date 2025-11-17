import discord
from discord import ui

from components.items import (
    ModalSelectComponent,
    SimpleLabelTextInput,
    SimpleSeparator,
    TitleTextDisplay,
)
from components.modals import SimpleModal
from components.paginated_view import PaginatedLayoutView
from logic.homebrew import HomebrewData, HomebrewEntry, HomebrewEntryType
from logic.markdown import MDFile, wrapped_md_table_to_rich_table


class HomebrewEmbed(discord.Embed):
    def __init__(self, itr: discord.Interaction, entry: HomebrewEntry):
        subtitle = f"*{entry.select_description}*\n\n"
        formatted_description = ""
        if entry.description:
            formatted_description = wrapped_md_table_to_rich_table(entry.description)

        if len(formatted_description) < 4000 - len(subtitle) and entry.select_description:
            description = subtitle + formatted_description
        else:
            description = formatted_description

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
    name = SimpleLabelTextInput(label="Name", placeholder="Peanut")
    type = ModalSelectComponent(label="Type", options=HomebrewEntryType.options(), required=True)
    subtitle = SimpleLabelTextInput(
        label="Subtitle",
        placeholder="A small legume",
        required=False,
        max_length=80,
    )
    description = SimpleLabelTextInput(
        label="Description",
        placeholder="A peanut is a legume that is often mistaken for a nut.",
        max_length=4000,
        style=discord.TextStyle.paragraph,
    )

    def __init__(self, itr: discord.Interaction, md_file: MDFile | None):
        if md_file:
            if len(md_file.content) > 4000:
                raise ValueError(
                    "Markdown file's content exceeds exceeds character-limit!\nPlease use a file with less than 4000 characters."
                )
            self.name.input.default = md_file.title
            self.name.input.placeholder = self.format_placeholder(md_file.title)
            self.description.input.default = md_file.content
            self.description.input.placeholder = self.format_placeholder(md_file.content)
        super().__init__(itr=itr, title="Add new homebrew entry")

    async def on_submit(self, itr: discord.Interaction):
        self.log_inputs(itr)

        name = self.get_str(self.name)
        entry_type: HomebrewEntryType | None = self.get_choice(self.type, HomebrewEntryType)
        subtitle = self.get_str(self.subtitle)
        description = self.get_str(self.description)

        if not name:
            raise ValueError("Name is a required field.")
        if not description:
            raise ValueError("Description is a required field.")
        if not entry_type:
            raise ValueError("Type is a required field.")

        entry = HomebrewData.get(itr).add(itr, entry_type, name=name, select_description=subtitle, description=description)
        embed = HomebrewEmbed(itr, entry)
        await itr.response.send_message(content=f"Added {entry_type.value}: ``{name}``!", embed=embed, ephemeral=True)


class HomebrewEditModal(SimpleModal):
    entry: HomebrewEntry
    name = SimpleLabelTextInput(label="Name")
    subtitle = SimpleLabelTextInput(label="Subtitle", required=False, max_length=80)
    description = SimpleLabelTextInput(label="Description", max_length=4000, style=discord.TextStyle.paragraph)

    def __init__(self, itr: discord.Interaction, entry: HomebrewEntry):
        self.entry = entry
        self.name.input.default = entry.name
        self.name.input.placeholder = entry.name
        self.subtitle.input.default = entry.select_description or ""
        self.subtitle.input.placeholder = entry.select_description or "Subtitle"
        self.description.input.default = entry.description
        self.description.input.placeholder = self.format_placeholder(entry.description)
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

    def __init__(self, itr: discord.Interaction, filter: str | None):  # pylint: disable=redefined-builtin
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
