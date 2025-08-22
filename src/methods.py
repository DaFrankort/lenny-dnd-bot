import io
import rich
from rich.table import Table
from rich.console import Console


def when(condition: bool, value_on_true: any, value_on_false: any) -> any:
    """Wrapper method for a ternary statement, for readability"""
    return value_on_true if condition else value_on_false


def build_table(value, width: int | None = 56, show_lines: bool = False) -> str:
    def format_cell_value(value: int | str | object) -> str:
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
    table = Table(style=None, box=box_style, show_lines=show_lines)

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
