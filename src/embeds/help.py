import discord
from logic.help import HelpSelectOption, HelpTab, HelpTabs


class HelpSelect(discord.ui.Select):
    def __init__(self, embed: "HelpEmbed", options: list[HelpSelectOption]):
        self.embed = embed
        self.option_choices = [discord.SelectOption(value=option.value, label=option.label) for option in options]
        self.option_choices = sorted(self.option_choices, key=lambda o: o.label)

        super().__init__(
            placeholder="Select a help tab.",
            options=self.option_choices,
            min_values=1,
            max_values=1,
        )

    async def callback(self, itr: discord.Interaction):
        tab = self.values[0]
        tab = HelpTabs.find(tab)
        self.embed.load_tab(tab)
        return await itr.response.edit_message(embed=self.embed)


class HelpSelectView(discord.ui.View):
    def __init__(self, embed: any, options: list[HelpSelectOption]):
        super().__init__(timeout=360)
        self.add_item(HelpSelect(embed, options))


class HelpEmbed(discord.Embed):
    tree: discord.app_commands.CommandTree
    options: list[HelpSelectOption]
    view: HelpSelectView

    def __init__(self, tree: discord.app_commands.CommandTree, tab: str | None = None):
        super().__init__(color=discord.Color.dark_green())

        self.tree = tree
        self.options = [HelpSelectOption(tab.tab, tab.name) for tab in HelpTabs.tabs]
        self.view = HelpSelectView(self, self.options)

        found_tab = HelpTabs.find(tab)
        self.load_tab(found_tab)

    def _get_command_desc_line(self, cmd: discord.app_commands.Command | discord.app_commands.Group):
        if isinstance(cmd, discord.app_commands.Command):
            command_comm = cmd.command
            command_help = cmd.help
            return f"``{command_comm}``\n{command_help}\n"

        if isinstance(cmd, discord.app_commands.Group):
            group_desc = []
            for group_cmd in cmd.commands:
                desc = self._get_command_desc_line(group_cmd)
                group_desc.append(desc)

            return "\n".join(group_desc)

        raise NotImplementedError(f"app_command type '{type(cmd)}' not implemented in _get_command_desc_line!")

    def _iterate_commands(
        self, cmd_or_grp: discord.app_commands.Command | discord.app_commands.Group, command_name: str = ""
    ) -> list[str]:
        commands = []
        command_name = f"{command_name} {cmd_or_grp.name}".strip()

        if isinstance(cmd_or_grp, discord.app_commands.Command):
            commands.append(command_name)
        elif isinstance(cmd_or_grp, discord.app_commands.Group):
            for sub_cmd in cmd_or_grp.commands:
                commands.extend(self._iterate_commands(sub_cmd, command_name))
        else:
            raise NotImplementedError(f"app_command type '{type(cmd_or_grp)}' not implemented in _get_tab_commands_list!")
        return commands

    def load_tab(self, tab: HelpTab):
        self.clear_fields()

        name = tab.name
        self.title = f"Help - {name}"

        # List all commands
        commands = tab.commands
        commands_desc = []

        if tab.text is not None:
            commands_desc.append(tab.text + "\n")

        for com in commands:
            command: discord.app_commands.Command = self.tree.get_command(com)
            command_desc = self._get_command_desc_line(command)
            commands_desc.append(command_desc)

        self.add_field(name="", value="\n".join(commands_desc), inline=False)

        # Add extra info
        for info_name, info_fields in tab.info:
            if isinstance(info_fields, list):
                info_fields = "\n".join(info_fields)

            self.add_field(name=info_name, value=info_fields, inline=False)

        # If on overview tab, list all commands, grouped by category
        if tab.tab == "overview":
            tabs = [tab for tab in HelpTabs.tabs if tab.tab != "overview"]
            tabs_commands = []
            for tab in tabs:
                tab_commands = []
                for cmd in tab.commands:
                    cmd_or_grp = self.tree.get_command(cmd)
                    if cmd_or_grp is not None:
                        tab_commands.extend(self._iterate_commands(cmd_or_grp))

                cmds = [f"- ``/{command}``" for command in tab_commands]
                tabs_commands.append((tab.name, cmds))

            tabs_commands.sort(key=lambda t: (-len(t[1]), t[0]))

            for name, commands in tabs_commands:
                self.add_field(name=name, value="\n".join(commands), inline=True)

    @staticmethod
    def get_tab_choices() -> list[discord.app_commands.Choice]:
        choices: list[discord.app_commands.Choice] = []
        for tab in HelpTabs.tabs:
            name = tab.name
            choices.append(discord.app_commands.Choice(name=name, value=tab.tab))
        choices.sort(key=lambda c: c.name)
        return choices
