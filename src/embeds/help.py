import discord
from command import SimpleCommand, SimpleCommandGroup, SimpleContextMenu
from logic.help import HelpSelectOption, HelpTab, HelpTabs
from discord.app_commands import Command, Group, CommandTree, Choice


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

    async def callback(self, interaction: discord.Interaction):
        tab = self.values[0]
        tab = HelpTabs.find(tab)
        self.embed.load_tab(tab)
        return await interaction.response.edit_message(embed=self.embed)


class HelpSelectView(discord.ui.View):
    def __init__(self, embed: "HelpEmbed", options: list[HelpSelectOption]):
        super().__init__(timeout=360)
        self.add_item(HelpSelect(embed, options))


class HelpEmbed(discord.Embed):
    tree: CommandTree
    options: list[HelpSelectOption]
    view: HelpSelectView

    def __init__(self, tree: CommandTree, tab: str | None = None):
        super().__init__(color=discord.Color.dark_green())

        self.tree = tree
        self.options = [HelpSelectOption(tab.tab, tab.name) for tab in HelpTabs.tabs]
        self.view = HelpSelectView(self, self.options)

        found_tab = HelpTabs.find(tab)
        self.load_tab(found_tab)

    def _get_command_desc_line(self, cmd: SimpleCommand | SimpleCommandGroup | Command | Group) -> str:
        if isinstance(cmd, SimpleCommand):
            command_comm = cmd.command
            command_help = cmd.help
            return f"``{command_comm}``\n{command_help}\n"

        if isinstance(cmd, SimpleCommandGroup):
            group_desc = []
            commands = cmd.commands
            for group_cmd in commands:
                desc = self._get_command_desc_line(group_cmd)
                group_desc.append(desc)

            return "\n".join(group_desc)

        raise NotImplementedError(f"app_command type '{type(cmd)}' not implemented in _get_command_desc_line!")

    def _iterate_commands(self, cmd_or_grp: Command | Group) -> list[str]:
        commands = []

        if isinstance(cmd_or_grp, Command):
            commands.append(cmd_or_grp.qualified_name)
        elif isinstance(cmd_or_grp, Group):
            for sub_cmd in cmd_or_grp.commands:
                commands.extend(self._iterate_commands(sub_cmd))
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
            command = self.tree.get_command(com)
            if isinstance(command, (SimpleCommand, SimpleCommandGroup)):
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
            tabs = [tab for tab in HelpTabs.tabs if tab.tab not in ["overview", "context"]]
            tabs_commands = []
            for tab in tabs:
                tab_commands = []
                for cmd in tab.commands:
                    cmd_or_grp = self.tree.get_command(cmd)
                    if cmd_or_grp is not None:
                        tab_commands.extend(self._iterate_commands(cmd_or_grp))

                cmds = [f"- ``/{command}``" for command in tab_commands]
                tabs_commands.append((tab.name, cmds))

            context_cmds: list[str] = []
            for context in self.tree.walk_commands(type=discord.AppCommandType.message):
                if isinstance(context, SimpleContextMenu):
                    context_cmds.append(f"- ``{context.name}``")
            for context in self.tree.walk_commands(type=discord.AppCommandType.user):
                if isinstance(context, SimpleContextMenu):
                    context_cmds.append(f"- ``{context.name}``")

            if len(context_cmds) > 0:
                tabs_commands.append((HelpTabs.ContextMenus.name, context_cmds))

            tabs_commands.sort(key=lambda t: (-len(t[1]), t[0]))

            for name, commands in tabs_commands:
                self.add_field(name=name, value="\n".join(commands), inline=True)

        elif tab.tab == "context":
            msg_contexts: list[str] = []
            user_contexts: list[str] = []
            for context in self.tree.walk_commands(type=discord.AppCommandType.message):
                if isinstance(context, SimpleContextMenu):
                    name = f"``MESSAGE > APPS > {context.name}``"
                    desc = context.help
                    msg_contexts.append(f"{name}\n{desc}\n")

            for context in self.tree.walk_commands(type=discord.AppCommandType.user):
                if isinstance(context, SimpleContextMenu):
                    name = f"``USER > APPS > {context.name}``"
                    desc = context.help
                    user_contexts.append(f"{name}\n{desc}\n")

            if len(msg_contexts) > 0:
                self.add_field(name="Message contexts", value="\n".join(msg_contexts))
            if len(user_contexts) > 0:
                self.add_field(name="User contexts", value="\n".join(user_contexts))

    @staticmethod
    def get_tab_choices() -> list[Choice]:
        choices: list[Choice] = []
        for tab in HelpTabs.tabs:
            name = tab.name
            choices.append(Choice(name=name, value=tab.tab))
        choices.sort(key=lambda c: c.name)
        return choices
