import io
import discord
import rich
from rich.table import Table
from rich.console import Console
from discord import ui
from components.items import SimpleSeparator, TitleTextDisplay
from components.paginated_view import PaginatedLayoutView
from dnd import DNDTable
from embeds2 import UserActionEmbed
from logger import log_button_press
from methods import build_table_from_rows
from voice_chat import VC, SoundType


class DNDTableRollButton(ui.Button):
    def __init__(self, table: DNDTable):
        super().__init__(
            style=discord.ButtonStyle.primary, label="Roll", custom_id="roll_btn"
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


class DNDTableContainerView(PaginatedLayoutView):
    file: discord.File = None
    table: DNDTable
    tables: list[str]

    @property
    def max_pages(self) -> int:
        # The max pages are purely depended on the stringified tables
        return len(self.tables)

    def __init__(self, table: DNDTable):
        super().__init__()
        self.table = table
        self.tables = []

        # Calculate the longest sub-tables for the pagination
        # Not particularly optimal, but tables have a maximum of 100 rows
        # so it should be fast enough
        headers = self.table.table["value"]["headers"]
        rows = self.table.table["value"]["rows"]
        rows_end = len(rows)
        while len(rows) > 0:
            built = build_table_from_rows(headers, rows[:rows_end])
            if len(built) < 4000:
                self.tables.append(built)
                rows = rows[rows_end:]
                rows_end = len(rows)
            else:
                rows_end -= 1

        self.build()

    def build(self) -> None:
        self.clear_items()
        container = ui.Container(accent_color=discord.Color.dark_green())

        title_display = TitleTextDisplay(
            name=self.table.name, source=self.table.source, url=self.table.url
        )
        if self.table.is_rollable:
            title_section = ui.Section(
                title_display, accessory=DNDTableRollButton(self.table)
            )
            container.add_item(title_section)
        else:
            container.add_item(title_display)

        table_string = self.tables[self.page]
        table_display = ui.TextDisplay(table_string)
        container.add_item(table_display)

        if self.table.footnotes:
            for footnote in self.table.footnotes:
                container.add_item(ui.TextDisplay(f"-# {footnote}"))

        if len(self.tables) > 1:
            container.add_item(SimpleSeparator())
            container.add_item(self.navigation_footer())

        self.add_item(container)
