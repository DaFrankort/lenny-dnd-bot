import io
import discord
import rich
from rich.table import Table
from rich.console import Console
from discord import ui
from components.items import TitleTextDisplay
from dnd import DNDTable
from embeds import UserActionEmbed
from logger import log_button_press
from methods import build_table
from voice_chat import VC, SoundType


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

        table_string = build_table(table.table["value"])
        if len(table_string) < 4000:
            table_display = ui.TextDisplay(table_string)
            container.add_item(table_display)
        else:
            container.add_item(ui.TextDisplay("TODO: Handle large tables."))

        if table.footnotes:
            for footnote in table.footnotes:
                container.add_item(ui.TextDisplay(f"-# {footnote}"))

        self.add_item(container)
