import re
import dataclasses

import discord


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
    table_pattern = re.compile(r"((?:^\|.*\|\r?\n?)+)", re.MULTILINE)  # one or more table lines together

    def wrap_table(match):
        table_block = match.group(1).strip("\n")
        # Prevent double-wrapping if already in a code block
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
