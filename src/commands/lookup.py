import logging

import discord

from dnd import DNDData, DNDObject
from embeds import MultiDNDSelectView, NoResultsFoundEmbed
from logger import log_cmd
from search import SearchEmbed, search_from_query


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
        embed = found[0].get_embed()
        if isinstance(embed, discord.ui.LayoutView):  # Uses LayoutView instead of Embed
            await itr.response.send_message(view=embed)
            return
        view = getattr(embed, "view", discord.interactions.MISSING)
        await itr.response.send_message(embed=embed, view=view)


class LookupSpellCommand(discord.app_commands.Command):
    name = "spell"
    desc = "Get the details for a spell."
    help = "Looks up a spell by name."
    command = "/spell <spell name>"

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__(
            name=self.name,
            description=self.desc,
            callback=self.callback,
        )

    async def name_autocomplete(self, _: discord.Interaction, current: str):
        return self.data.spells.get_autocomplete_suggestions(query=current)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        log_cmd(itr)
        found = self.data.spells.get(name)
        await send_DNDObject_lookup_result(itr, "spells", found, name)


class LookupItemCommand(discord.app_commands.Command):
    name = "item"
    desc = "Get the details for an item."
    help = "Looks up an item by name."
    command = "/item <item name>"

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__(
            name=self.name,
            description=self.desc,
            callback=self.callback,
        )

    async def name_autocomplete(self, _: discord.Interaction, current: str):
        return self.data.items.get_autocomplete_suggestions(query=current)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        log_cmd(itr)
        found = self.data.items.get(name)
        await send_DNDObject_lookup_result(itr, "items", found, name)


class LookupConditionCommand(discord.app_commands.Command):
    name = "condition"
    desc = "Get the details of a condition or status effect."
    help = "Looks up a condition or status effect by name."
    command = "/condition <condition name>"

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__(
            name=self.name,
            description=self.desc,
            callback=self.callback,
        )

    async def name_autocomplete(self, _: discord.Interaction, current: str):
        return self.data.conditions.get_autocomplete_suggestions(query=current)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        log_cmd(itr)
        found = self.data.conditions.get(name)
        await send_DNDObject_lookup_result(itr, "conditions", found, name)


class LookupCreatureCommand(discord.app_commands.Command):
    name = "creature"
    desc = "Get the details of a creature."
    help = "Looks up a creature by name."
    command = "/creature <creature name>"

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__(
            name=self.name,
            description=self.desc,
            callback=self.callback,
        )

    async def name_autocomplete(self, _: discord.Interaction, current: str):
        return self.data.creatures.get_autocomplete_suggestions(query=current)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        log_cmd(itr)
        found = self.data.creatures.get(name)
        await send_DNDObject_lookup_result(itr, "creatures", found, name)


class LookupClassCommand(discord.app_commands.Command):
    name = "class"
    desc = "Get the details for a character class."
    help = "Looks up a D&D class by name."
    command = "/class <class name>"

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__(
            name=self.name,
            description=self.desc,
            callback=self.callback,
        )

    async def name_autocomplete(self, _: discord.Interaction, current: str):
        return self.data.classes.get_autocomplete_suggestions(query=current)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        log_cmd(itr)
        found = self.data.classes.get(name)
        await send_DNDObject_lookup_result(itr, "classes", found, name)


class LookupRuleCommand(discord.app_commands.Command):
    name = "rule"
    desc = "Get the details of a D&D rule."
    help = "Looks up a D&D rule by name."
    command = "/rule <rule name>"

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__(
            name=self.name,
            description=self.desc,
            callback=self.callback,
        )

    async def name_autocomplete(self, _: discord.Interaction, current: str):
        return self.data.rules.get_autocomplete_suggestions(query=current)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        log_cmd(itr)
        found = self.data.rules.get(name)
        await send_DNDObject_lookup_result(itr, "rules", found, name)


class LookupActionCommand(discord.app_commands.Command):
    name = "action"
    desc = "Get the details of a D&D action."
    help = "Looks up a D&D action by name."
    command = "/action <action name>"

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__(
            name=self.name,
            description=self.desc,
            callback=self.callback,
        )

    async def name_autocomplete(self, _: discord.Interaction, current: str):
        return self.data.actions.get_autocomplete_suggestions(query=current)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        log_cmd(itr)
        found = self.data.actions.get(name)
        await send_DNDObject_lookup_result(itr, "actions", found, name)


class LookupFeatCommand(discord.app_commands.Command):
    name = "feat"
    desc = "Get the details of a character feat."
    help = "Looks up a character feat by name."
    command = "/feat <feat name>"

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__(
            name=self.name,
            description=self.desc,
            callback=self.callback,
        )

    async def name_autocomplete(self, _: discord.Interaction, current: str):
        return self.data.feats.get_autocomplete_suggestions(query=current)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        log_cmd(itr)
        found = self.data.feats.get(name)
        await send_DNDObject_lookup_result(itr, "feats", found, name)


class LookupLanguageCommand(discord.app_commands.Command):
    name = "language"
    desc = "Get the details of a language."
    help = "Looks up a D&D Language by name."
    command = "/language <language name>"

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__(
            name=self.name,
            description=self.desc,
            callback=self.callback,
        )

    async def name_autocomplete(self, _: discord.Interaction, current: str):
        return self.data.languages.get_autocomplete_suggestions(query=current)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        log_cmd(itr)
        found = self.data.languages.get(name)
        await send_DNDObject_lookup_result(itr, "languages", found, name)


class LookupBackgroundCommand(discord.app_commands.Command):
    name = "background"
    desc = "Get the details of a background."
    help = "Looks up a D&D Background by name."
    command = "/background <background name>"

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__(
            name=self.name,
            description=self.desc,
            callback=self.callback,
        )

    async def name_autocomplete(self, _: discord.Interaction, current: str):
        return self.data.backgrounds.get_autocomplete_suggestions(query=current)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        log_cmd(itr)
        found = self.data.backgrounds.get(name)
        await send_DNDObject_lookup_result(itr, "background", found, name)


class LookupTableCommand(discord.app_commands.Command):
    name = "table"
    desc = "Get the details of a table."
    help = "Looks up a D&D Table by name."
    command = "/table <table name>"

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__(
            name=self.name,
            description=self.desc,
            callback=self.callback,
        )

    async def name_autocomplete(self, _: discord.Interaction, current: str):
        return self.data.tables.get_autocomplete_suggestions(query=current)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        log_cmd(itr)
        found = self.data.tables.get(name)
        await send_DNDObject_lookup_result(itr, "table", found, name)


class LookupSpeciesCommand(discord.app_commands.Command):
    name = "species"
    desc = "Get the details of a species."
    help = "Looks up a D&D Species by name."
    command = "/species <species name>"

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__(
            name=self.name,
            description=self.desc,
            callback=self.callback,
        )

    async def name_autocomplete(self, _: discord.Interaction, current: str):
        return self.data.species.get_autocomplete_suggestions(query=current)

    @discord.app_commands.autocomplete(name=name_autocomplete)
    async def callback(self, itr: discord.Interaction, name: str):
        log_cmd(itr)
        found = self.data.species.get(name)
        await send_DNDObject_lookup_result(itr, "species", found, name)


class LookupAnyCommand(discord.app_commands.Command):
    name = "search"
    desc = "Search for a D&D entry."
    help = "Looks up all possible D&D entries for a query."
    command = "/search <query>"

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__(
            name=self.name,
            description=self.desc,
            callback=self.callback,
        )

    async def callback(self, itr: discord.Interaction, query: str):
        log_cmd(itr)
        results = search_from_query(query, self.data)
        logging.debug(f"Found {len(results.get_all())} results for '{query}'")

        if len(results.get_all()) == 0:
            embed = NoResultsFoundEmbed("results", query)
            await itr.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = SearchEmbed(query, results)
            await itr.response.send_message(
                embed=embed, view=embed.view, ephemeral=True
            )
