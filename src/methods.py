from enum import Enum
import io
import logging
from typing import Iterable, TypeVar
import rich
import rich.box
from rich.table import Table
from rich.console import Console
from PIL import ImageFont

T = TypeVar("T")
U = TypeVar("U")


def when(condition: bool | str | int | None, value_on_true: T, value_on_false: U) -> T | U:
    """Wrapper method for a ternary statement, for readability"""
    return value_on_true if condition else value_on_false


def build_table(value, width: int | None = 56, show_lines: bool = False) -> str:
    def format_cell_value(value: int | str | dict) -> str:
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

    headers = value["headers"]
    rows = value["rows"]

    box_style = rich.box.SQUARE_DOUBLE_HEAD if show_lines else rich.box.ROUNDED
    table = Table(box=box_style, show_lines=show_lines)

    for header in headers:
        table.add_column(header, justify="left", style=None)

    for row in rows:
        formatted_row = [format_cell_value(value) for value in row]
        table.add_row(*formatted_row)

    buffer = io.StringIO()
    console = Console(file=buffer, width=width)
    console.print(table)
    table_string = f"```{buffer.getvalue()}```"
    buffer.close()

    return table_string


def build_table_from_rows(
    headers: list[str],
    rows: list[Iterable[str]],
    width: int | None = 56,
    show_lines: bool = False,
) -> str:
    return build_table({"headers": headers, "rows": rows}, width, show_lines)


class FontType(Enum):
    MONOSPACE = "./assets/fonts/GoogleSansCode-Light.ttf"
    FANTASY = "./assets/fonts/Merienda-Light.ttf"


def get_font(font: FontType, size: float):
    try:
        return ImageFont.truetype(font=font.value, size=size)
    except OSError:
        logging.warning(f"Font '{font.value}' could not be loaded!")
        return ImageFont.load_default(size=size)
