import discord
from discord import ui
from components.items import SimpleSeparator, TitleTextDisplay
from components.paginated_view import PaginatedLayoutView
from logic.homebrew import DNDHomebrewObject, HomebrewData
from modals import SimpleModal


class HomebrewEmbed(discord.Embed):
    view: ui.View = None

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
        label="Subtitle",
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

        entry = HomebrewData.get(itr).add(itr, self.dnd_type, name=name, select_description=subtitle, description=description)
        embed = HomebrewEmbed(itr, entry)
        await itr.response.send_message(content=f"Added {self.dnd_type}: ``{name}``!", embed=embed, ephemeral=True)


class HomebrewEditModal(SimpleModal):
    entry: DNDHomebrewObject
    name = ui.TextInput(label="Name")
    subtitle = ui.TextInput(label="Subtitle", required=False, max_length=80)
    description = ui.TextInput(label="Description", max_length=4000, style=discord.TextStyle.paragraph)

    def __init__(self, entry: DNDHomebrewObject):
        self.entry = entry
        self.name.default = entry.name
        self.name.placeholder = entry.name
        self.subtitle.default = entry.select_description or ""
        self.subtitle.placeholder = entry.select_description or "Subtitle"
        self.description.default = entry.description
        self.description.placeholder = entry.description[:97] + "..." if len(entry.description) > 97 else entry.description
        super().__init__(itr=None, title=f"Edit {entry.object_type}: {entry.name}")

    async def on_submit(self, itr: discord.Interaction):
        self.log_inputs(itr)

        name = self.get_str(self.name)
        subtitle = self.get_str(self.subtitle)
        description = self.get_str(self.description)

        if not name or not description:
            await itr.response.send_message("Name and Description are required fields.", ephemeral=True)
            return

        # TODO DELETE ORIGINAL
        entry = HomebrewData.get(itr).add(itr, self.dnd_type, name=name, select_description=subtitle, description=description)
        embed = HomebrewEmbed(itr, entry)
        await itr.response.send_message(
            content=f"Edited {self.entry.object_type}: ``{self.entry.name}`` => ``{name}``!", embed=embed, ephemeral=True
        )


class HomebrewListView(PaginatedLayoutView):
    filter: str
    entries: list[DNDHomebrewObject]

    def __init__(self, itr: discord.Interaction, filter: str | None):
        self.filter = None
        label = "All Entries"
        if filter is not None:
            self.filter = filter
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
        container = ui.Container(accent_color=discord.Color.blue())

        # HEADER
        container.add_item(self.title_item)
        container.add_item(SimpleSeparator())

        # CONTENT
        options = self.get_current_options()
        for option in options:
            container.add_item(ui.TextDisplay(option.name))

        # FOOTER
        container.add_item(SimpleSeparator())
        container.add_item(self.navigation_footer())

        self.add_item(container)
