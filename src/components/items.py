from discord import ui
from dnd import Description
from methods import when


class TitleTextDisplay(ui.TextDisplay):
    """A TextDisplay which is formatted as a title, with optional source and URL."""

    def __init__(self, name: str, source: str = None, url: str = None, id=None):
        title = when(source, f"{name} ({source})", name)
        title = when(url, f"[{title}]({url})", title)
        title = f"# {title}"
        super().__init__(content=title, id=id)


class FieldTextDisplay(ui.TextDisplay):
    """A TextDisplay that formats the text as a field, with a label and value."""

    def __init__(self, name: str, value: str, id=None):
        content = when(name, f"### {name}\n{value}", value)
        super().__init__(content=content, id=id)

    @classmethod
    def from_description(cls, description: Description, id=None):
        """
        Build a FieldTextDisplay from a Description object.

        Args:
            description: An object with 'name' and 'value' attributes.
            id: Optional ID for the UI element.
        """
        name = description["name"]
        value = description["value"]
        type = description["type"]

        if type == "table":
            # TODO BUILD TABLE
            return cls(name=name, value=value, id=id)
        return cls(name=name, value=value, id=id)


class SimpleSeparator(ui.Separator):
    def __init__(self, is_large=False):
        if is_large:
            super().__init__(spacing=ui.SeparatorSpacing.large)
        else:
            super().__init__(spacing=ui.SeparatorSpacing.small)
