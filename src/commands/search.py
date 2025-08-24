import logging

import discord

from app_commands import SimpleCommand, SimpleCommandGroup
from config import Config
from dnd import DNDData, DNDObject, send_dnd_embed
from embeds import MultiDNDSelectView, NoResultsFoundEmbed
from search import SearchLayoutView


async def send_DNDObject_lookup_result(
    itr: discord.Interaction,
    label: str,
    found: list[DNDObject],
    name: str,
):
    """Helper function to send generic D&D lookup embeds and views."""
    logging.debug(f"{label.upper()}: Found {len(found)} for '{name}'")

    if len(found) == 0:
        embed = NoResultsFoundEmbed(label, name)
        await itr.response.send_message(embed=embed, ephemeral=True)

    elif len(found) > 1:
        view = MultiDNDSelectView(name, found)
        await itr.response.send_message(view=view, ephemeral=True)

    else:
        await send_dnd_embed(itr, found[0])


class SearchSpellCommand(SimpleCommand):
    name = "spell"
    desc = "Get the details for a spell."
    help = "Looks up a spell by name."

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__()

    async def name_autocomplete(self, itr: discord.Interaction, current: str):
        sources = Config.allowed_sources(server=itr.guild)
        return self.data.spells.get_autocomplete_suggestions(current, sources)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.allowed_sources(server=itr.guild)
        found = self.data.spells.get(name, sources)
        await send_DNDObject_lookup_result(itr, "spells", found, name)


class SearchItemCommand(SimpleCommand):
    name = "item"
    desc = "Get the details for an item."
    help = "Looks up an item by name."

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__()

    async def name_autocomplete(self, itr: discord.Interaction, current: str):
        sources = Config.allowed_sources(server=itr.guild)
        return self.data.items.get_autocomplete_suggestions(current, sources)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.allowed_sources(server=itr.guild)
        found = self.data.items.get(name, sources)
        await send_DNDObject_lookup_result(itr, "items", found, name)


class SearchConditionCommand(SimpleCommand):
    name = "condition"
    desc = "Get the details of a condition or status effect."
    help = "Looks up a condition or status effect by name."

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__()

    async def name_autocomplete(self, itr: discord.Interaction, current: str):
        sources = Config.allowed_sources(server=itr.guild)
        return self.data.conditions.get_autocomplete_suggestions(current, sources)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.allowed_sources(server=itr.guild)
        found = self.data.conditions.get(name, sources)
        await send_DNDObject_lookup_result(itr, "conditions", found, name)


class SearchCreatureCommand(SimpleCommand):
    name = "creature"
    desc = "Get the details of a creature."
    help = "Looks up a creature by name."

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__()

    async def name_autocomplete(self, itr: discord.Interaction, current: str):
        sources = Config.allowed_sources(server=itr.guild)
        return self.data.creatures.get_autocomplete_suggestions(current, sources)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.allowed_sources(server=itr.guild)
        found = self.data.creatures.get(name, sources)
        await send_DNDObject_lookup_result(itr, "creatures", found, name)


class SearchClassCommand(SimpleCommand):
    name = "class"
    desc = "Get the details for a character class."
    help = "Looks up a D&D class by name."

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__()

    async def name_autocomplete(self, itr: discord.Interaction, current: str):
        sources = Config.allowed_sources(server=itr.guild)
        return self.data.classes.get_autocomplete_suggestions(current, sources)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.allowed_sources(server=itr.guild)
        found = self.data.classes.get(name, sources)
        await send_DNDObject_lookup_result(itr, "classes", found, name)


class SearchRuleCommand(SimpleCommand):
    name = "rule"
    desc = "Get the details of a D&D rule."
    help = "Looks up a D&D rule by name."

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__()

    async def name_autocomplete(self, itr: discord.Interaction, current: str):
        sources = Config.allowed_sources(server=itr.guild)
        return self.data.rules.get_autocomplete_suggestions(current, sources)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.allowed_sources(server=itr.guild)
        found = self.data.rules.get(name, sources)
        await send_DNDObject_lookup_result(itr, "rules", found, name)


class SearchActionCommand(SimpleCommand):
    name = "action"
    desc = "Get the details of a D&D action."
    help = "Looks up a D&D action by name."

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__()

    async def name_autocomplete(self, itr: discord.Interaction, current: str):
        sources = Config.allowed_sources(server=itr.guild)
        return self.data.actions.get_autocomplete_suggestions(current, sources)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.allowed_sources(server=itr.guild)
        found = self.data.actions.get(name, sources)
        await send_DNDObject_lookup_result(itr, "actions", found, name)


class SearchFeatCommand(SimpleCommand):
    name = "feat"
    desc = "Get the details of a character feat."
    help = "Looks up a character feat by name."

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__()

    async def name_autocomplete(self, itr: discord.Interaction, current: str):
        sources = Config.allowed_sources(server=itr.guild)
        return self.data.feats.get_autocomplete_suggestions(current, sources)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.allowed_sources(server=itr.guild)
        found = self.data.feats.get(name, sources)
        await send_DNDObject_lookup_result(itr, "feats", found, name)


class SearchLanguageCommand(SimpleCommand):
    name = "language"
    desc = "Get the details of a language."
    help = "Looks up a D&D Language by name."

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__()

    async def name_autocomplete(self, itr: discord.Interaction, current: str):
        sources = Config.allowed_sources(server=itr.guild)
        return self.data.languages.get_autocomplete_suggestions(current, sources)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.allowed_sources(server=itr.guild)
        found = self.data.languages.get(name, sources)
        await send_DNDObject_lookup_result(itr, "languages", found, name)


class SearchBackgroundCommand(SimpleCommand):
    name = "background"
    desc = "Get the details of a background."
    help = "Looks up a D&D Background by name."

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__()

    async def name_autocomplete(self, itr: discord.Interaction, current: str):
        sources = Config.allowed_sources(server=itr.guild)
        return self.data.backgrounds.get_autocomplete_suggestions(current, sources)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.allowed_sources(server=itr.guild)
        found = self.data.backgrounds.get(name, sources)
        await send_DNDObject_lookup_result(itr, "background", found, name)


class SearchTableCommand(SimpleCommand):
    name = "table"
    desc = "Get the details of a table."
    help = "Looks up a D&D Table by name."

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__()

    async def name_autocomplete(self, itr: discord.Interaction, current: str):
        sources = Config.allowed_sources(server=itr.guild)
        return self.data.tables.get_autocomplete_suggestions(current, sources)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.allowed_sources(server=itr.guild)
        found = self.data.tables.get(name, sources)
        await send_DNDObject_lookup_result(itr, "table", found, name)


class SearchSpeciesCommand(SimpleCommand):
    name = "species"
    desc = "Get the details of a species."
    help = "Looks up a D&D Species by name."

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__()

    async def name_autocomplete(self, itr: discord.Interaction, current: str):
        sources = Config.allowed_sources(server=itr.guild)
        return self.data.species.get_autocomplete_suggestions(current, sources)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.allowed_sources(server=itr.guild)
        found = self.data.species.get(name, sources)
        await send_DNDObject_lookup_result(itr, "species", found, name)


class SearchAnyCommand(SimpleCommand):
    name = "all"
    desc = "Search for all matching D&D entries."
    help = "Looks up all possible D&D entries for a query."

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__()

    async def callback(self, itr: discord.Interaction, query: str):
        self.log(itr)
        sources = Config.allowed_sources(server=itr.guild)
        results = self.data.search(query, sources)
        logging.debug(f"Found {len(results.get_all())} results for '{query}'")

        if len(results.get_all()) == 0:
            embed = NoResultsFoundEmbed("results", query)
            await itr.response.send_message(embed=embed, ephemeral=True)
        else:
            view = SearchLayoutView(query, results)
            await itr.response.send_message(view=view, ephemeral=True)


class SearchCommandGroup(SimpleCommandGroup):
    name = "search"
    desc = "Search for a D&D entry."

    def __init__(self, data: DNDData):
        super().__init__()
        self.add_command(SearchSpellCommand(data=data))
        self.add_command(SearchItemCommand(data=data))
        self.add_command(SearchConditionCommand(data=data))
        self.add_command(SearchCreatureCommand(data=data))
        self.add_command(SearchClassCommand(data=data))
        self.add_command(SearchRuleCommand(data=data))
        self.add_command(SearchActionCommand(data=data))
        self.add_command(SearchFeatCommand(data=data))
        self.add_command(SearchLanguageCommand(data=data))
        self.add_command(SearchBackgroundCommand(data=data))
        self.add_command(SearchTableCommand(data=data))
        self.add_command(SearchSpeciesCommand(data=data))
        self.add_command(SearchAnyCommand(data=data))
