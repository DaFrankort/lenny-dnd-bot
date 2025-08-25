import io
import discord
import rich
from rich.table import Table
from rich.console import Console
from discord import ui
from components.items import SimpleSeparator, TitleTextDisplay
from dnd import DNDTable
from embeds import UserActionEmbed
from logger import log_button_press
from methods import FontType, build_table, get_font
from voice_chat import VC, SoundType
from PIL import Image, ImageDraw


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


class DNDTableContainerView(ui.LayoutView):
    file: discord.File = None

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
            container.add_item(SimpleSeparator())

            table_string = build_table(
                table.table["value"], 112, True
            )  # Rebuild table, but wider
            font_size = 64
            padding = font_size // 2
            font = get_font(FontType.MONOSPACE, font_size)
            lines = table_string.replace("```", "").splitlines()

            # Calculate image dimensions
            max_width = max([font.getlength(line) for line in lines])
            line_height = int((font.getbbox("A")[3] - font.getbbox("A")[1]) * 1.5)
            img_height = line_height * len(lines) + 4 * padding
            img_width = int(max_width) + 4 * padding

            # Draw image with text
            img = Image.new("RGB", (img_width, img_height), color=(10, 10, 25))
            draw = ImageDraw.Draw(img)
            y = padding
            for line in lines:
                draw.text((padding * 2, y), line, font=font, fill="white")
                y += line_height

            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            self.file = discord.File(
                fp=buffer, filename=table.name.lower().replace(" ", "_") + ".png"
            )

            container.add_item(
                ui.MediaGallery(discord.MediaGalleryItem(media=self.file))
            )

        if table.footnotes:
            for footnote in table.footnotes:
                container.add_item(ui.TextDisplay(f"-# {footnote}"))

        self.add_item(container)
