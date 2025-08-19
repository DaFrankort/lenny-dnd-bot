import dataclasses
import discord

from i18n import t
import i18n
from logger import log_cmd


@dataclasses.dataclass
class HelpSelectOption(object):
    value: str
    label: str


def get_tab_base_commands_list(tab: str) -> list[str]:
    commands = []
    for command in t(f"help.{tab}.commands"):
        command = t(f"commands.{command}.command")
        command = command.split(" ")[0]  # Remove arguments
        commands.append(command)
    return commands


class HelpSelect(discord.ui.Select):
    def __init__(self, embed: any, options: list[HelpSelectOption]):
        self.embed = embed
        self.option_choices = [
            discord.SelectOption(value=option.value, label=option.label)
            for option in options
        ]
        self.option_choices = sorted(self.option_choices, key=lambda o: o.label)

        super().__init__(
            placeholder="Select a help tab.",
            options=self.option_choices,
            min_values=1,
            max_values=1,
        )

    async def callback(self, itr: discord.Interaction):
        tab = self.values[0]
        self.embed.load_tab(tab)
        return await itr.response.edit_message(embed=self.embed)


class HelpSelectView(discord.ui.View):
    def __init__(self, embed: any, options: list[HelpSelectOption]):
        super().__init__(timeout=360)
        self.add_item(HelpSelect(embed, options))


class HelpEmbed(discord.Embed):
    tabs: list[str] = [
        "overview",
        "roll",
        "dnd",
        "initiative",
        "character",
        "tokengen",
        "utility",
    ]
    tab: str
    options: list[HelpSelectOption]
    view: HelpSelectView

    def __init__(self, tab: str | None = None):
        super().__init__(color=discord.Color.dark_green())

        self.tab = tab or "overview"
        self.options = [
            HelpSelectOption(tab, t(f"help.{tab}.name")) for tab in HelpEmbed.tabs
        ]
        self.view = HelpSelectView(self, self.options)
        self.load_tab(self.tab)

    def load_tab(self, tab: str):
        self.clear_fields()

        name = t(f"help.{tab}.name")
        self.title = f"Help - {name}"

        # List all commands
        commands = t(f"help.{tab}.commands")
        commands_desc = []

        if i18n.has(f"help.{tab}.text"):
            commands_desc.append(t(f"help.{tab}.text") + "\n")

        for command in commands:
            command_comm = t(f"commands.{command}.command")
            command_help = t(f"commands.{command}.help")
            commands_desc.append(f"``{command_comm}``\n{command_help}\n")

        self.add_field(name="", value="\n".join(commands_desc), inline=False)

        # Add extra info
        info_i = 0
        while True:
            if not i18n.has(f"help.{tab}.info.{info_i}"):
                break

            info_name = t(f"help.{tab}.info.{info_i}.name")
            info_fields = t(f"help.{tab}.info.{info_i}.info")

            if isinstance(info_fields, list):
                info_fields = "\n".join(info_fields)

            self.add_field(name=info_name, value=info_fields, inline=False)
            info_i += 1

        # If on overview tab, list all commands, grouped by category
        if tab == "overview":
            categories = [tab for tab in HelpEmbed.tabs if tab != "overview"]
            categories_commands = []
            for category in categories:
                category_name = t(f"help.{category}.name")
                category_commands = get_tab_base_commands_list(category)
                category_commands = [
                    f"``- {command}``" for command in category_commands
                ]
                categories_commands.append((category_name, category_commands))

            categories_commands.sort(key=lambda t: (-len(t[1]), t[0]))

            for name, commands in categories_commands:
                self.add_field(name=name, value="\n".join(commands), inline=True)

    @staticmethod
    def get_tab_choices() -> list[discord.app_commands.Choice]:
        choices: list[discord.app_commands.Choice] = []
        for tab in HelpEmbed.tabs:
            name = t(f"help.{tab}.name")
            choices.append(discord.app_commands.Choice(name=name, value=tab))
        choices.sort(key=lambda c: c.name)
        return choices


class HelpCommand(discord.app_commands.Command):
    name = t("commands.help.name")
    description = t("commands.help.desc")

    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.description,
            callback=self.callback,
        )

    @discord.app_commands.choices(tab=HelpEmbed.get_tab_choices())
    async def callback(self, itr: discord.Interaction, tab: str = None):
        log_cmd(itr)
        embed = HelpEmbed(tab)
        await itr.response.send_message(embed=embed, view=embed.view, ephemeral=True)
