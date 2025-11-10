import re
import dataclasses
import discord
from typing import Iterable
from logic.dnd.abstract import build_table_from_rows


def wrapped_md_table_to_rich_table(text: str) -> str:
    """
    Detects markdown tables wrapped in triple backticks (```),
    parses them, builds Rich tables using build_table_from_rows(),
    and replaces them in the text.
    """
    code_table_pattern = re.compile(r"```(?:[^\n]*)?\n((?:\|.*\|\n?)+)```", re.MULTILINE)  # capture just the table content

    def split_row(row: str) -> Iterable[str]:
        """Split a markdown table row into cells."""
        return [cell.strip() for cell in row.strip("|").split("|")]

    def parse_table(md_table: str) -> tuple[list[str], list[Iterable[str]]]:
        """Parse markdown table text into headers and rows."""
        lines = [
            line.strip()
            for line in md_table.strip().splitlines()
            if line.strip().startswith("|") and line.strip().endswith("|")
        ]
        if len(lines) < 2:
            return [], []

        headers: list[str] = list(split_row(lines[0]))
        data_lines = lines[2:] if len(lines) > 2 else []
        rows: list[Iterable[str]] = [split_row(line) for line in data_lines]

        return headers, rows

    def replace_with_rich_table(match: re.Match[str]) -> str:
        md_table = match.group(1)
        headers, rows = parse_table(md_table)
        if not headers:
            return match.group(0)
        rich_table = build_table_from_rows(headers=headers, rows=rows)
        return str(rich_table)

    text = code_table_pattern.sub(replace_with_rich_table, text)

    return text


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
    table_pattern = re.compile(r"((?:^\|.*\|\r?\n?)+)", re.MULTILINE)

    def wrap_table(match: re.Match[str]) -> str:
        table_block = match.group(1).strip("\n")
        if table_block.startswith("```"):
            return match.group(0)
        return f"```\n{table_block}\n```"

    text = table_pattern.sub(wrap_table, text)
    return text


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
