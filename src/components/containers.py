from abc import abstractmethod
import io
import discord
import rich
from rich.table import Table
from rich.console import Console
from discord import ui
from components.items import SimpleSeparator, TitleTextDisplay
from dnd import DNDObject, DNDTable, Description
from embeds import UserActionEmbed
from logger import log_button_press
from voice_chat import VC, SoundType


class _LookupContainerView(ui.LayoutView):
    """
    Superclass for DNDObject-Containers that helps ensure data stays within Discord's character limits.
    Additionally provides functions to handle Description-field & Table generation.
    """

    container: ui.Container = None
    _object: DNDObject
    view: ui.View = None

    def __init__(self, object: DNDObject, subtitle_item: ui.Item = None):
        self._object = object
        super().__init__(timeout=None)
        self.container = ui.Container(accent_color=self.get_color())

        title = f"{object.name} ({object.source})"
        title = f"# [{title}]({object.url})" if object.url else f"# {title}"
        self.container.add_item(ui.TextDisplay(title))

        if subtitle_item:
            self.container.add_item(subtitle_item)
        elif object.select_description:
            subtitle = f"-# **{object.select_description}**"
            self.container.add_item(ui.TextDisplay(subtitle))

        self.container.add_item(SimpleSeparator())
        self.add_item(self.container)

    def _rebuild_container(self):
        self.remove_item(self.container)
        self.add_item(self.container)

    @abstractmethod
    def get_color(self) -> discord.Color:
        """
        Returns the color for the embed, based on the object's type or other criteria.
        If not overridden, defaults to a dark green color.
        """
        return discord.Color.dark_green()

    @property
    def char_count(self):
        """The total amount of characters currently in the embed."""

        char_count = (
            (len(self.title) if self.title else 0)
            + (len(self.description) if self.description else 0)
            + (len(self.footer.text) if self.footer and self.footer.text else 0)
            + (len(self.author.name) if self.author else 0)
        )

        if self.fields:
            for field in self.fields:
                char_count += len(field.name) + len(field.value)

        return char_count

    def _format_cell_value(self, value: int | str | object) -> str:
        if isinstance(value, int):
            return str(value)
        elif isinstance(value, str):
            return value
        elif value["type"] == "range":
            if value["min"] == value["max"]:
                return str(value["min"])
            else:
                return f"{value['min']}-{value['max']}"
        raise Exception("Unsupported cell type")

    def build_table(self, value, CHAR_FIELD_LIMIT=1024) -> str:
        """Turns a Description with headers & rows into a clean table using rich."""

        headers = value["headers"]
        rows = value["rows"]
        table = Table(style=None, box=rich.box.ROUNDED)

        for header in headers:
            table.add_column(header, justify="left", style=None)

        for row in rows:
            formatted_row = [self._format_cell_value(value) for value in row]
            table.add_row(*formatted_row)

        buffer = io.StringIO()
        console = Console(file=buffer, width=56)
        console.print(table)
        table_string = f"```{buffer.getvalue()}```"
        buffer.close()

        if len(table_string) > CHAR_FIELD_LIMIT:
            return f"The table for [{self._object.name} can be found here]({self._object.url})."
        return table_string

    def _get_field_text(self, name: str, value: str) -> str:
        """Formats the field text with a header if the name is not empty."""
        if name.strip():
            return f"### {name}\n{value}"
        return value

    def add_container_item(self, item: ui.Item):
        """Adds a single item to the container."""
        self.container.add_item(item)
        self._rebuild_container()

    def add_field(self, name: str, value: str):
        field = ui.TextDisplay(self._get_field_text(name, value))
        self.container.add_item(field)
        self._rebuild_container()

    def add_description_field(self, Description: Description, ignore_tables=False):
        name = Description["name"]
        value = Description["value"]
        type = Description["type"]

        if type == "table" and not ignore_tables:
            value = self.build_table(value)

        self.add_field(name, value)

    def add_description_fields(
        self,
        descriptions: list[Description],
        ignore_tables=False,
    ):
        for description in descriptions:
            self.add_description_field(description, ignore_tables=ignore_tables)


class DNDTableRollButton(ui.Button):
    def __init__(self, table: DNDTable):
        label = f"Roll {table.dice_notation}"
        super().__init__(
            style=discord.ButtonStyle.primary, label=label, custom_id="roll_btn"
        )
        self.table = table

    async def callback(self, itr: discord.Interaction):
        log_button_press(
            itr=itr, button=self, location=f"Table Roll - {self.table.name}"
        )
        row, expression = self.table.roll()
        if row is None or expression is None:
            # Disable button to prevent further attempts, since it will keep failing.
            self.disabled = True
            self.style = discord.ButtonStyle.gray
            await itr.response.send_message(
                "❌ Couldn't roll table, something went wrong. ❌"
            )
            await itr.message.edit(view=self)
            return

        console_table = Table(style=None, box=rich.box.ROUNDED)
        # Omit the first header and first row value
        for header in self.table.table["value"]["headers"][1:]:
            console_table.add_column(header, justify="left", style=None)
        console_table.add_row(*row[1:])

        buffer = io.StringIO()
        console = Console(file=buffer, width=56)
        console.print(console_table)
        description = f"```{buffer.getvalue()}```"
        buffer.close()

        embed = UserActionEmbed(itr=itr, title=expression.title, description="")
        embed.description = description
        embed.title = f"{self.table.name} [{expression.roll.value}]"
        await itr.response.send_message(embed=embed)
        await VC.play(itr, sound_type=SoundType.ROLL)


class DNDTableContainerView(ui.LayoutView):
    def __init__(self, table: DNDTable):
        super().__init__(timeout=None)
        container = ui.Container(accent_color=discord.Color.dark_green())

        title_display = TitleTextDisplay(
            name=table.name, source=table.source, url=table.url
        )
        if table.is_rollable:
            title_section = ui.Section(
                title_display, accessory=DNDTableRollButton(table)
            )
            container.add_item(title_section)
        else:
            container.add_item(title_display)

        container.add_item(
            ui.TextDisplay("```TODO: TABLE HERE```")
        )  # TODO ADD TABLE BUILDING
        self.add_item(container)
