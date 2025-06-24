import dataclasses
import discord
import i18n


@dataclasses.dataclass
class HelpSelectOption(object):
    value: str
    label: str


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
        "color",
        "character",
        "tokengen",
    ]
    tab: str
    options: list[HelpSelectOption]
    view: HelpSelectView

    def __init__(self, tab: str | None = None):
        super().__init__(color=discord.Color.dark_green())

        self.tab = tab or "overview"
        self.options = [
            HelpSelectOption(tab, i18n.t(f"help.{tab}.name")) for tab in HelpEmbed.tabs
        ]
        self.view = HelpSelectView(self, self.options)
        self.load_tab(self.tab)

    def load_tab(self, tab: str):
        self.clear_fields()

        name = i18n.t(f"help.{tab}.name")
        self.title = f"Help - {name}"

        # List all commands
        commands = i18n.t(f"help.{tab}.commands")
        commands_desc = []

        if i18n.has(f"help.{tab}.text"):
            commands_desc.append(i18n.t(f"help.{tab}.text") + "\n")

        for command in commands:
            command_comm = i18n.t(f"commands.{command}.command")
            command_help = i18n.t(f"commands.{command}.help")
            commands_desc.append(f"``{command_comm}``\n{command_help}\n")

        self.add_field(name="", value="\n".join(commands_desc), inline=False)

        # Add extra info
        for info_i in range(100):
            if not i18n.has(f"help.{tab}.info.{info_i}"):
                break

            info_name = i18n.t(f"help.{tab}.info.{info_i}.name")
            info_fields = i18n.t(f"help.{tab}.info.{info_i}.info")

            if isinstance(info_fields, list):
                info_fields = "\n".join(info_fields)

            self.add_field(name=info_name, value=info_fields, inline=False)
