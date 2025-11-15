import discord
from discord.app_commands import Choice, CommandTree, Group

from commands.command import SimpleCommand, SimpleCommandGroup, SimpleContextMenu
from logic.help import HelpSelectOption, HelpTab, HelpTabs


class HelpSelect(discord.ui.Select["HelpSelectView"]):
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

    @classmethod
    def _get_commands(cls, group: Group) -> list[SimpleCommand | SimpleCommandGroup]:
        commands: list[SimpleCommand | SimpleCommandGroup] = []
        for command in group.commands:
            if isinstance(command, (SimpleCommand, SimpleCommandGroup)):
                commands.append(command)
        return commands

    def _get_command_desc_line(self, cmd: SimpleCommand | SimpleCommandGroup) -> str:
        if isinstance(cmd, SimpleCommand):
            command_comm = cmd.command
            command_help = cmd.help
            return f"``{command_comm}``\n{command_help}\n"

        # SimpleCommandGroup
        group_desc: list[str] = []
        commands = self._get_commands(cmd)
        for group_cmd in commands:
            desc = self._get_command_desc_line(group_cmd)
            group_desc.append(desc)

        return "\n".join(group_desc)

    def _iterate_commands(self, cmd: SimpleCommand | SimpleCommandGroup) -> list[str]:
        commands: list[str] = []

        if isinstance(cmd, SimpleCommand):
            commands.append(cmd.qualified_name)
        # SimpleCommandGroup
        else:
            for sub_cmd in self._get_commands(cmd):
                commands.extend(self._iterate_commands(sub_cmd))
        return commands

    def load_tab(self, tab: HelpTab):
        self.clear_fields()
        self.title = f"Help - {tab.name}"

        self._load_tab_commands(tab)

        if tab.tab == "overview":
            self._load_overview_tab()

        if tab.tab == "context":
            self._load_context_tab()

    def _load_tab_commands(self, tab: HelpTab) -> None:
        command_names = tab.commands
        commands_desc: list[str] = []

        if tab.text is not None:
            commands_desc.append(tab.text + "\n")

        for command_name in command_names:
            command = self.tree.get_command(command_name)
            if isinstance(command, (SimpleCommand, SimpleCommandGroup)):
                command_desc = self._get_command_desc_line(command)
                commands_desc.append(command_desc)

        commands_parts: list[str] = []
        for desc in commands_desc:
            length = len("\n".join(commands_parts)) + len(desc)
            if length > 1024:
                self.add_field(name="", value="\n".join(commands_parts), inline=False)
                commands_parts = []
            commands_parts.append(desc)
        if commands_parts:
            self.add_field(name="", value="\n".join(commands_parts), inline=False)

        # Add extra info
        for info_name, info_fields in tab.info:
            if isinstance(info_fields, list):
                info_fields = "\n".join(info_fields)

            self.add_field(name=info_name, value=info_fields, inline=False)

    def _load_overview_tab(self) -> None:
        tabs_to_ignore = ["overview", "context"]
        tabs = [tab for tab in HelpTabs.tabs if tab.tab not in tabs_to_ignore]
        tabs_commands: list[tuple[str, list[str]]] = []
        for tab in tabs:
            tab_commands: list[str] = []
            for cmd in tab.commands:
                cmd = self.tree.get_command(cmd)
                # Only handle SimpleCommand and SimpleCommandGroup, any other commands are ill-formed
                if cmd is not None and isinstance(cmd, (SimpleCommand, SimpleCommandGroup)):
                    tab_commands.extend(self._iterate_commands(cmd))

            cmds = [f"- ``/{command}``" for command in tab_commands]
            tabs_commands.append((tab.name, cmds))

        # Add context menu overview
        context_cmds = [
            f"- ``{ctx.name}``"
            for ctx_type in (discord.AppCommandType.message, discord.AppCommandType.user)
            for ctx in self.tree.walk_commands(type=ctx_type)
            if isinstance(ctx, SimpleContextMenu)
        ]
        if context_cmds:
            tabs_commands.append((HelpTabs.ContextMenus.name, context_cmds))

        tabs_commands.sort(key=lambda t: (-len(t[1]), t[0]))

        for name, commands in tabs_commands:
            self.add_field(name=name, value="\n".join(commands), inline=True)

    def _load_context_tab(self) -> None:
        msg_contexts: list[str] = []
        user_contexts: list[str] = []

        # load message contexts
        for context in self.tree.walk_commands(type=discord.AppCommandType.message):
            if isinstance(context, SimpleContextMenu):
                name = f"``MESSAGE > APPS > {context.name}``"
                desc = context.help
                msg_contexts.append(f"{name}\n{desc}\n")

        # load user contexts
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
    def get_tab_choices() -> list[Choice[str]]:
        choices: list[Choice[str]] = []
        for tab in HelpTabs.tabs:
            name = tab.name
            choices.append(Choice(name=name, value=tab.tab))
        choices.sort(key=lambda c: c.name)
        return choices
