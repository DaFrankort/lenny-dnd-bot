import re
import dataclasses

import discord


def format_markdown_to_discord(text: str) -> str:
    """Removes markdown formatting that is not compatible with discord."""
    while "####" in text:
        text = text.replace("####", "###")  # unsupported header formats: ### is max header
    text = re.sub(r"\[\[(.*?)\]\]", r"\1", text)  # Obsidian file links: [[FILE]]
    text = re.sub(r"\[([^\]]+)\]\[[^\]]*\]", r"\1", text)  # Reference links: [FILENAME][FILEPATH]

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
