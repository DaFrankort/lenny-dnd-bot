import dataclasses
import discord

from logic.app_commands import SimpleCommand


@dataclasses.dataclass
class HelpSelectOption(object):
    value: str
    label: str


@dataclasses.dataclass
class HelpTab(object):
    tab: str
    name: str
    commands: list[str]
    text: str | None
    info: list[tuple[str, list[str] | str]]


class HelpTabList(object):
    Overview = HelpTab(
        tab="overview",
        name="Overview",
        commands=["help"],
        text=None,
        info=[
            (
                "Additional Info",
                [
                    "You can get more information for each command by navigating to its category help tab."
                ],
            )
        ],
    )

    Roll = HelpTab(
        tab="roll",
        name="Roll",
        commands=[
            "roll",
            "d20",
            "advantage",
            "disadvantage",
            "shortcut",
            "distribution",
        ],
        text="You can roll dice using the following commands:",
        info=[
            (
                "Dice Notations",
                [
                    "To roll dice, you need to use dice notations, these generally follow the `XdY + Z` format.",
                    "For example, ``1d20 + 6`` rolls a single 20-sided die and adds 6 to the result, these notations are expandable to combine a large number of dice.",
                    "Besides basic math operators (``+``, ``-``, ``/``, ``*``), ``NdN`` and numbers, you can also use modifiers [documented on this site.](https://d20.readthedocs.io/en/latest/start.html#grammar)",
                    "*Note: Dice notations are sometimes referred to as dice expressions instead.*",
                ],
            ),
            (
                "Shortcuts",
                [
                    "Shortcuts let you save dice rolls or modifiers you use frequently under a custom name, so you don't have to type out the full notation each time.",
                    '- For example, if you often roll **1d8+3+2d6** for a sneak attack, you can create a shortcut called "SNEAK".',
                    '- Once you\'ve saved a shortcut, you can use it in any dice expression like so ``/roll "SNEAK"``.',
                    '- You can also use your shortcuts within expressions, like so: ``/roll "SNEAK+5"``, this will evaluate to **1d8+3+1d6__+5__**',
                    "- Shortcuts can also have default roll reasons. This reason will be used whenever you use the shortcut, unless you specify another reason.",
                ],
            ),
            (
                "Sound Effects",
                [
                    "If FFMPEG is installed, the bot will play sound effects for rolls, by default these are basic dice-rolling sounds.",
                    "A handful of reasons or events may trigger a special sound effect, these are the following:",
                    "- *Critical Hit* - When a 1d20 results to 20, a critical hit sound is played.",
                    "- *Critical Fail* - When a 1d20 results to 1, a critical fail sound is played.",
                    "- *Attack* - If the specified reason is `attack`, an attack sound is played.",
                    "- *Damage* - If the specified reason is `damage`, a damage sound is played.",
                    "- *Fire* - If the specified reason is `fire`, a fire sound is played.",
                ],
            ),
        ],
    )

    Utility = HelpTab(
        tab="utility",
        name="Discord Utilities",
        commands=["color", "plansession", "playsound", "timestamp"],
        text=None,
        info=[
            (
                "User Colors",
                [
                    "By default, a random color is generated depending on the user's display name.",
                    "These colors are used in action commands (e.g. /roll), making it quicker to discern which player did which action.",
                ],
            )
        ],
    )

    Character = HelpTab(
        tab="character",
        name="Character Utilities",
        commands=["stats", "namegen"],
        text="You can easily generate stats and names for your character using the following commands:",
        info=[],
    )

    DND = HelpTab(
        tab="dnd",
        name="D&D Resources",
        commands=["search"],
        text="You can look up D&D information from [5e.tools](https://5e.tools/) using the following commands:",
        info=[],
    )

    Initiative = HelpTab(
        tab="initiative",
        name="Initiative",
        commands=["initiative"],
        text="You can track initiatives for combat using the following command:",
        info=[
            (
                "Player Buttons",
                [
                    "The top row of buttons are mainly meant for players, these include:",
                    "- ``Roll``: Roll a value by providing your __initiative modifier__ in the popup. Optionally you can provide a roll mode by typing A for Advantage and D for Disadvantage and you can roll for a creature by specifying a creature name.",
                    "- ``Set``: Set your initiative value to a specific __value__. Optionally you can specify a name to set another creature's initiative value.",
                    "- ``Delete Roll``: Remove your roll from the initiatives. Optionally you can specify a name to remove another creature's initiative.",
                ],
            ),
            (
                "DM Buttons",
                [
                    "The bottom row of buttons have features which are handy for the Dungeon Master.",
                    "- ``Bulk``: Roll Initiatives in bulk for multiple creatures by specifying their __modifiers__, __names__ and the __amount__ of creatures to add. Optionally can roll with Advantage or Disadvantage or specify to use the same initiative value for all the creatures.",
                    "- ``Lock``: Disables all the other buttons, to prevent users from accidentally pressing any more buttons.",
                    "- ``Clear Rolls``: Clears all the initiatives, to be used after combat.",
                ],
            ),
            (
                "Notes",
                [
                    "Upon calling ``/initiative`` it will assure other initiative messages won't get interacted with.",
                    "- If the previous message is younger than 10 minutes it will be deleted.",
                    "- If it is older, the buttons to interact with it will be deleted.",
                ],
            ),
        ],
    )

    TokenGen = HelpTab(
        tab="tokengen",
        name="Token Generation",
        commands=["tokengen", "tokengenurl"],
        text="You can generate token images for your characters or creatures in the 5e.tools style using the following commands:",
        info=[
            (
                "Image Adjustments",
                [
                    "There are a few options to adjust the way a token image is generated, by default it will provide a golden border and center the provided image.",
                    "However you can use the following options to adjust the way the token is generated:",
                    "- ``hue-shift`` - Allows you to shift the color of the token's border, this is a number between -360 and 360. By default a shift of 0 is used, which results in a golden border.",
                    "- ``h_alignment`` - Adjusts the horizontal alignment of the image, this can be `left`, `center`, or `right`.",
                    "- ``v_alignment`` - Adjusts the vertical alignment of the image, this can be `top`, `center`, or `bottom`.",
                ],
            )
        ],
    )

    Config = HelpTab(
        tab="config",
        name="Bot configuration",
        commands=["config"],
        text="You can configure the bot behavior in your server using the following commands:",
        info=[
            (
                "Server Configuration",
                [
                    "The bot can only be configured in servers and will always use the default settings in private messages."
                ],
            )
        ],
    )

    @property
    def tabs(self) -> list[HelpTab]:
        return [
            self.Overview,
            self.Roll,
            self.Utility,
            self.Character,
            self.DND,
            self.Initiative,
            self.Config,
        ]

    @property
    def keys(self) -> list[str]:
        return [tab.tab for tab in self.tabs]

    def find(self, tab: str | None) -> HelpTab:
        if tab is None:
            return self.Overview
        for t in self.tabs:
            if t.tab == tab:
                return t
        raise Exception(f"help: tab '{tab}' not found.")


HelpTabs = HelpTabList()


class HelpSelect(discord.ui.Select):
    def __init__(self, embed: "HelpEmbed", options: list[HelpSelectOption]):
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

    def _get_command_desc_line(
        self, cmd: discord.app_commands.Command | discord.app_commands.Group
    ):
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

        raise NotImplementedError(
            f"app_command type '{type(cmd)}' not implemented in _get_command_desc_line!"
        )

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
                tab_commands = [f"``- {command}``" for command in tab.commands]
                tabs_commands.append((tab.name, tab_commands))

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


class HelpCommand(SimpleCommand):
    name = "help"
    desc = "Get an overview of all commands."
    help = "Show the help tab for the given section. If no section is provided, this overview is given."

    tree: discord.app_commands.CommandTree

    def __init__(self, tree: discord.app_commands.CommandTree):
        self.tree = tree
        super().__init__()

    @discord.app_commands.choices(tab=HelpEmbed.get_tab_choices())
    async def callback(self, itr: discord.Interaction, tab: str = None):
        self.log(itr)
        embed = HelpEmbed(self.tree, tab=tab)
        await itr.response.send_message(embed=embed, view=embed.view, ephemeral=True)
