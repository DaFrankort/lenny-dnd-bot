import csv
import dataclasses
import io
import re
from collections.abc import Sequence

import discord

from logic.dnd.abstract import build_table_from_rows


def _parse_md_table_csv(md_table: str) -> tuple[list[str], Sequence[Sequence[str]]]:
    lines = [
        line.strip() for line in md_table.strip().splitlines() if line.strip().startswith("|") and line.strip().endswith("|")
    ]
    if len(lines) < 2:
        return [], []

    # Use csv.reader to split on pipes
    def split_line(line: str) -> Sequence[str]:
        reader = csv.reader(io.StringIO(line.strip("|")), delimiter="|")
        return [cell.strip() for row in reader for cell in row]

    headers = list(split_line(lines[0]))
    data_lines = lines[2:] if len(lines) > 2 else []
    rows = [split_line(line) for line in data_lines]
    return headers, rows


def wrapped_md_table_to_rich_table(text: str) -> str:
    """
    Detects markdown tables wrapped in triple backticks (```),
    parses them, builds Rich tables using build_table_from_rows(),
    and replaces them in the text.
    """
    parts = text.split("```")
    new_parts: list[str] = []

    for part in parts:
        stripped = part.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            headers, rows = _parse_md_table_csv(stripped)
            if headers:
                rich_table = build_table_from_rows(headers=headers, rows=rows)
                part = str(rich_table)  # pylint: disable=redefined-loop-name
        new_parts.append(part)

    return "".join(new_parts)


def _wrap_markdown_tables(text: str) -> str:
    """
    Wraps obsidian tables into codeblocks, for it to be monospace
    Table formatting is as follows:

    | 1d4 | Element |
    | --- | ------- |
    | 1   | Earth   |
    | 2   | Fire    |
    | 3   | Water   |
    | 4   | Air     |
    """
    lines = text.splitlines()
    new_lines: list[str] = []
    inside_table = False
    buffer: list[str] = []

    def flush_table():
        if buffer:
            table_text = "\n".join(buffer)
            new_lines.append("```")
            new_lines.append(table_text)
            new_lines.append("```")
            buffer.clear()

    for line in lines:
        if line.strip().startswith("|") and line.strip().endswith("|"):
            inside_table = True
            buffer.append(line)
        else:
            if inside_table:
                flush_table()
                inside_table = False
            new_lines.append(line)

    if inside_table:
        flush_table()

    return "\n".join(new_lines)


def format_markdown_to_discord(text: str) -> str:
    """Removes markdown formatting that is not compatible with discord."""
    while "####" in text:
        text = text.replace("####", "###")  # unsupported header formats: ### is max header
    text = re.sub(r"\[\[(.*?)\]\]", r"\1", text)  # Obsidian file links: [[FILE]]
    text = re.sub(r"\[([^\]]+)\]\[[^\]]*\]", r"\1", text)  # Reference links: [FILENAME][FILEPATH]
    text = _wrap_markdown_tables(text)

    return text


@dataclasses.dataclass
class MDFile:
    title: str
    content: str

    @classmethod
    async def from_attachment(cls, file: discord.Attachment):
        if not file.content_type:
            raise ValueError("Attached file has unknown filetype.")
        if "text/markdown" not in file.content_type:
            raise ValueError("Attached file must be a .md file.")

        file_bytes = await file.read()
        title = file.filename.replace(".md", "").replace("_", " ")
        content = file_bytes.decode("utf-8")
        content = format_markdown_to_discord(content)
        return cls(title, content)
