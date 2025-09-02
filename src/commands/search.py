import logging

import discord

from logic.app_commands import SimpleCommand, SimpleCommandGroup
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

    async def name_autocomplete(self, itr: discord.Interaction, current: str):
        sources = Config.allowed_sources(server=itr.guild)
        return DNDData.instance().spells.get_autocomplete_suggestions(current, sources)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.allowed_sources(server=itr.guild)
        found = DNDData.instance().spells.get(name, sources)
        await send_DNDObject_lookup_result(itr, "spells", found, name)


class SearchItemCommand(SimpleCommand):
    name = "item"
    desc = "Get the details for an item."
    help = "Looks up an item by name."

    async def name_autocomplete(self, itr: discord.Interaction, current: str):
        sources = Config.allowed_sources(server=itr.guild)
        return DNDData.instance().items.get_autocomplete_suggestions(current, sources)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.allowed_sources(server=itr.guild)
        found = DNDData.instance().items.get(name, sources)
        await send_DNDObject_lookup_result(itr, "items", found, name)


class SearchConditionCommand(SimpleCommand):
    name = "condition"
    desc = "Get the details of a condition or status effect."
    help = "Looks up a condition or status effect by name."

    async def name_autocomplete(self, itr: discord.Interaction, current: str):
        sources = Config.allowed_sources(server=itr.guild)
        return DNDData.instance().conditions.get_autocomplete_suggestions(
            current, sources
        )

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.allowed_sources(server=itr.guild)
        found = DNDData.instance().conditions.get(name, sources)
        await send_DNDObject_lookup_result(itr, "conditions", found, name)


class SearchCreatureCommand(SimpleCommand):
    name = "creature"
    desc = "Get the details of a creature."
    help = "Looks up a creature by name."

    async def name_autocomplete(self, itr: discord.Interaction, current: str):
        sources = Config.allowed_sources(server=itr.guild)
        return DNDData.instance().creatures.get_autocomplete_suggestions(
            current, sources
        )

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.allowed_sources(server=itr.guild)
        found = DNDData.instance().creatures.get(name, sources)
        await send_DNDObject_lookup_result(itr, "creatures", found, name)


class SearchClassCommand(SimpleCommand):
    name = "class"
    desc = "Get the details for a character class."
    help = "Looks up a D&D class by name."

    async def name_autocomplete(self, itr: discord.Interaction, current: str):
        sources = Config.allowed_sources(server=itr.guild)
        return DNDData.instance().classes.get_autocomplete_suggestions(current, sources)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.allowed_sources(server=itr.guild)
        found = DNDData.instance().classes.get(name, sources)
        await send_DNDObject_lookup_result(itr, "classes", found, name)


class SearchRuleCommand(SimpleCommand):
    name = "rule"
    desc = "Get the details of a D&D rule."
    help = "Looks up a D&D rule by name."

    async def name_autocomplete(self, itr: discord.Interaction, current: str):
        sources = Config.allowed_sources(server=itr.guild)
        return DNDData.instance().rules.get_autocomplete_suggestions(current, sources)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.allowed_sources(server=itr.guild)
        found = DNDData.instance().rules.get(name, sources)
        await send_DNDObject_lookup_result(itr, "rules", found, name)


class SearchActionCommand(SimpleCommand):
    name = "action"
    desc = "Get the details of a D&D action."
    help = "Looks up a D&D action by name."

    async def name_autocomplete(self, itr: discord.Interaction, current: str):
        sources = Config.allowed_sources(server=itr.guild)
        return DNDData.instance().actions.get_autocomplete_suggestions(current, sources)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.allowed_sources(server=itr.guild)
        found = DNDData.instance().actions.get(name, sources)
        await send_DNDObject_lookup_result(itr, "actions", found, name)


class SearchFeatCommand(SimpleCommand):
    name = "feat"
    desc = "Get the details of a character feat."
    help = "Looks up a character feat by name."

    async def name_autocomplete(self, itr: discord.Interaction, current: str):
        sources = Config.allowed_sources(server=itr.guild)
        return DNDData.instance().feats.get_autocomplete_suggestions(current, sources)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.allowed_sources(server=itr.guild)
        found = DNDData.instance().feats.get(name, sources)
        await send_DNDObject_lookup_result(itr, "feats", found, name)


class SearchLanguageCommand(SimpleCommand):
    name = "language"
    desc = "Get the details of a language."
    help = "Looks up a D&D Language by name."

    async def name_autocomplete(self, itr: discord.Interaction, current: str):
        sources = Config.allowed_sources(server=itr.guild)
        return DNDData.instance().languages.get_autocomplete_suggestions(
            current, sources
        )

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.allowed_sources(server=itr.guild)
        found = DNDData.instance().languages.get(name, sources)
        await send_DNDObject_lookup_result(itr, "languages", found, name)


class SearchBackgroundCommand(SimpleCommand):
    name = "background"
    desc = "Get the details of a background."
    help = "Looks up a D&D Background by name."

    async def name_autocomplete(self, itr: discord.Interaction, current: str):
        sources = Config.allowed_sources(server=itr.guild)
        return DNDData.instance().backgrounds.get_autocomplete_suggestions(
            current, sources
        )

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.allowed_sources(server=itr.guild)
        found = DNDData.instance().backgrounds.get(name, sources)
        await send_DNDObject_lookup_result(itr, "background", found, name)


class SearchTableCommand(SimpleCommand):
    name = "table"
    desc = "Get the details of a table."
    help = "Looks up a D&D Table by name."

    async def name_autocomplete(self, itr: discord.Interaction, current: str):
        sources = Config.allowed_sources(server=itr.guild)
        return DNDData.instance().tables.get_autocomplete_suggestions(current, sources)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.allowed_sources(server=itr.guild)
        found = DNDData.instance().tables.get(name, sources)
        await send_DNDObject_lookup_result(itr, "table", found, name)


class SearchSpeciesCommand(SimpleCommand):
    name = "species"
    desc = "Get the details of a species."
    help = "Looks up a D&D Species by name."

    async def name_autocomplete(self, itr: discord.Interaction, current: str):
        sources = Config.allowed_sources(server=itr.guild)
        return DNDData.instance().species.get_autocomplete_suggestions(current, sources)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.allowed_sources(server=itr.guild)
        found = DNDData.instance().species.get(name, sources)
        await send_DNDObject_lookup_result(itr, "species", found, name)


class SearchAnyCommand(SimpleCommand):
    name = "all"
    desc = "Search for all matching D&D entries."
    help = "Looks up all possible D&D entries for a query."

    async def callback(self, itr: discord.Interaction, query: str):
        self.log(itr)
        sources = Config.allowed_sources(server=itr.guild)
        results = DNDData.search(query, sources)
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

    def __init__(self):
        super().__init__()
        self.add_command(SearchSpellCommand())
        self.add_command(SearchItemCommand())
        self.add_command(SearchConditionCommand())
        self.add_command(SearchCreatureCommand())
        self.add_command(SearchClassCommand())
        self.add_command(SearchRuleCommand())
        self.add_command(SearchActionCommand())
        self.add_command(SearchFeatCommand())
        self.add_command(SearchLanguageCommand())
        self.add_command(SearchBackgroundCommand())
        self.add_command(SearchTableCommand())
        self.add_command(SearchSpeciesCommand())
        self.add_command(SearchAnyCommand())
