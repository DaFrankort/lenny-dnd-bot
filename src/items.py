import json
import logging
import re
import discord
from rapidfuzz import fuzz


class Item(object):
    name: str
    source: str
    url: str
    value: str | None
    weight: str | None
    type: list[str]
    properties: list[str]
    description: list[tuple[str, str]]

    def __init__(self, json: any):
        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]
        self.value = json["value"]
        self.weight = json["weight"]
        self.type = json["type"]
        self.properties = json["properties"]
        self.description = json["description"]

    @property
    def is_phb2014(self) -> bool:
        return self.source == "PHB" or self.source == "DMG"


class ItemList(object):
    path = "./submodules/lenny-dnd-data/generated/items.json"

    items: list[Item] = []

    def __init__(self):
        with open(self.path, "r") as file:
            data = json.load(file)
            for item in data:
                self.items.append(Item(item))

    def get(
        self, name: str, ignore_phb2014: bool = True, fuzzy_threshold: float = 75
    ) -> list[Item]:
        logging.debug(
            f"Item: getting '{name}' (Ignoring PHB'14 = {ignore_phb2014}, threshold = {fuzzy_threshold / 100})"
        )
        name = name.strip().lower()
        exact = []
        fuzzy = []

        for item in self.items:
            if ignore_phb2014 and item.is_phb2014:
                continue

            item_name = item.name.strip().lower()
            if name == item_name:
                exact.append(item)
            elif fuzz.ratio(name, item_name) >= fuzzy_threshold:
                fuzzy.append(item)

        if len(exact) > 0:
            return exact
        return fuzzy


class ItemEmbed(discord.Embed):
    item: Item

    def __init__(self, item: Item) -> None:
        self.item = item

        title = f"{self.item.name} ({self.item.source})"
        super().__init__(
            title=title,
            type="rich",
            color=discord.Color.dark_green(),
            url=self.item.url,
        )

        value_weight = []
        if self.item.value is not None:
            value_weight.append(self.item.value)
        if self.item.weight is not None:
            value_weight.append(self.item.weight)
        if len(value_weight) == 0:
            value_weight = None
        else:
            value_weight = ", ".join(value_weight)

        if len(self.item.type) > 0:
            type = ", ".join(self.item.type).capitalize()
            type = f"*{type}*"
            self.add_field(name="", value=type, inline=False)

        if len(self.item.properties) > 0:
            properties = ", ".join(self.item.properties).capitalize()
            self.add_field(name="", value=properties, inline=False)

        if value_weight is not None:
            self.add_field(name="", value=value_weight, inline=False)

        if len(self.item.description) > 0:
            # Add horizontal line
            self.add_field(
                name="",
                value="~~-------------------------------------------------------------------------------------~~",
                inline=False,
            )

            for desc in self.item.description:
                self.add_field(name=desc["name"], value=desc["text"], inline=False)


class MultiItemSelect(discord.ui.Select):
    """A class representing a Discord select menu for multiple item selection."""

    query: str
    items: list[Item]

    def __init__(self, query: str, items: list[Item]):
        self.query = query
        self.items = items

        options = []
        for item in items:
            options.append(
                discord.SelectOption(
                    label=f"{item.name} ({item.source})",
                )
            )

        super().__init__(
            placeholder=f"Results for '{query}'",
            options=options,
            min_values=1,
            max_values=1,
        )

        logging.debug(f"MultiItemSelect: found {len(items)} items for '{query}'")

    async def callback(self, interaction: discord.Interaction):
        """Handles the selection of a item from the select menu."""
        full_name = self.values[0]
        name_pattern = r"^(.+) \(([^\)]+)\)"  # "Name (Source)"
        name_match = re.match(name_pattern, full_name)
        name = name_match.group(1)
        source = name_match.group(2)

        item = [
            item for item in self.items if item.name == name and item.source == source
        ][0]
        logging.debug(
            f"MultiItemSelect: user {interaction.user.display_name} selected '{name}"
        )
        await interaction.response.send_message(embed=ItemEmbed(item))


class NoItemsFoundEmbed(discord.Embed):
    """A class representing a Discord embed for when no items are found."""

    def __init__(self, query: str):
        super().__init__(
            color=discord.Color.dark_green(),
            title="No items found.",
            type="rich",
            url=None,
            description=None,
            timestamp=None,
        )
        self.add_field(name="", value=f"No items found for '{query}'.")


class MultiItemSelectView(discord.ui.View):
    """A class representing a Discord view for multiple spell selection."""

    def __init__(self, query: str, items: list[Item]):
        super().__init__()
        self.add_item(MultiItemSelect(query, items))
