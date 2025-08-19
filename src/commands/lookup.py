import logging

import discord

from dnd import DNDData, DNDObject
from embeds import MultiDNDSelectView, NoResultsFoundEmbed
from i18n import t
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
        view = embed.view
        if view:
            await itr.response.send_message(embed=embed, view=view)
            return
        await itr.response.send_message(embed=embed)


class LookupSpellCommand(discord.app_commands.Command):
    name = t("commands.spell.name")
    description = t("commands.spell.desc")

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__(
            name=self.name,
            description=self.description,
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
    name = t("commands.item.name")
    description = t("commands.item.desc")

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__(
            name=self.name,
            description=self.description,
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
    name = t("commands.condition.name")
    description = t("commands.condition.desc")

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__(
            name=self.name,
            description=self.description,
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
    name = t("commands.creature.name")
    description = t("commands.creature.desc")

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__(
            name=self.name,
            description=self.description,
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
    name = t("commands.class.name")
    description = t("commands.class.desc")

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__(
            name=self.name,
            description=self.description,
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
    name = t("commands.rule.name")
    description = t("commands.rule.desc")

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__(
            name=self.name,
            description=self.description,
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
    name = t("commands.action.name")
    description = t("commands.action.desc")

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__(
            name=self.name,
            description=self.description,
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
    name = t("commands.feat.name")
    description = t("commands.feat.desc")

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__(
            name=self.name,
            description=self.description,
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
    name = t("commands.language.name")
    description = t("commands.language.desc")

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__(
            name=self.name,
            description=self.description,
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
    name = t("commands.background.name")
    description = t("commands.background.desc")

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__(
            name=self.name,
            description=self.description,
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
    name = t("commands.table.name")
    description = t("commands.table.desc")

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__(
            name=self.name,
            description=self.description,
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
    name = t("commands.species.name")
    description = t("commands.species.desc")

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__(
            name=self.name,
            description=self.description,
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
    name = t("commands.search.name")
    description = t("commands.search.desc")

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__(
            name=self.name,
            description=self.description,
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
