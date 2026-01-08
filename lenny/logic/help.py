import dataclasses


@dataclasses.dataclass
class HelpSelectOption:
    value: str
    label: str


@dataclasses.dataclass
class HelpTab:
    tab: str
    name: str
    commands: list[str]
    text: str | None
    info: list[tuple[str, list[str] | str]]


class HelpTabList:
    Overview = HelpTab(
        tab="overview",
        name="Overview",
        commands=["help"],
        text=None,
        info=[
            (
                "Additional Info",
                ["You can get more information for each command by navigating to its category help tab."],
            )
        ],
    )

    ContextMenus = HelpTab(
        tab="context",
        name="Context Menus",
        commands=[],
        text="When you right click on a user or message and navigate to Apps you can perform the following actions:",
        info=[],
    )

    Roll = HelpTab(
        tab="roll",
        name="Roll",
        commands=[
            "roll",
            "d20",
            "advantage",
            "disadvantage",
            "multiroll",
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
        commands=["stats", "namegen", "charactergen"],
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

    Homebrew = HelpTab(
        tab="homebrew",
        name="D&D Homebrew",
        commands=["homebrew"],
        text="You can create custom information to use in your D&D sessions.",
        info=[
            (
                "Permissions",
                [
                    "A user can edit or remove homebrew entries if they are the author of that entry.",
                    "If a user has the ``Manage Messages`` permission they can edit or remove any homebrew entry.",
                    "If a user is an admin or they have permission granted in ``/config permissions`` they may also manage homebrew content.",
                ],
            ),
            (
                "Markdown Support",
                [
                    "When creating a homebrew entry, you can drag a ``.md`` (Markdown) file into the ``/homebrew add`` command.",
                    "The bot will automatically import the contents, convert the formatting, and make it compatible with Discord's display system.",
                    "Supported Markdown features include:",
                    "- **Headers:** Up to level 3 (``###``) — higher levels are automatically adjusted.",
                    "- **File Links:** Obsidian-style links like ``[[filename]]`` or reference links like ``[Name][Path]`` are converted to plain text.",
                    "- **Tables:** Obsidian-style tables (``| --- | --- |``) are formatted as monospace code blocks for clean display in Discord.",
                ],
            ),
            (
                "External URLs",
                [
                    "You can add a link to an external website when creating a Homebrew entry. If a URL is provided, the title of the Homebrew entry becomes clickable.",
                    "All URLs are checked for correct formatting. If the text you enter is not a valid URL, it may not be saved.",
                ],
            ),
        ],
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
        commands=["tokengen"],
        text="You can generate token images for your characters or creatures in the 5e.tools style using the following commands:",
        info=[
            (
                "Image Adjustments",
                [
                    "There are a few options to adjust the way a token image is generated, by default it will provide a golden border and center the provided image.",
                    "However you can use the following options to adjust the way the token is generated:",
                    "- ``hue-shift`` - Allows you to shift the color of the token's border, this is a number between -360 and 360. By default a shift of 0 is used, which results in a golden border.",
                    "- ``h_alignment`` - Adjusts the horizontal alignment of the image, this can be `left`, `center`, `right`, or `face`.",
                    "- ``v_alignment`` - Adjusts the vertical alignment of the image, this can be `top`, `center`, `bottom`, or `face`.",
                    "- ``variants`` - Creates up to 10 variants of the token image, to easily discern similar tokens from each other.",
                ],
            ),
            (
                "Alignment Face Detection",
                [
                    "You can detect and center the token on your character's facial features by using the `Face` alignment-option.",
                    "This is experimental; results are most accurate for portraits with clear, front-facing features.",
                    "The algorithm searches for human faces first, falling back to profile views, feline features, eyes, or full-body silhouettes if needed.",
                    "If no features were detected at all this will return an error-message.",
                ],
            ),
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
                    "The bot can only be configured in servers and will always use the default settings in private messages.",
                    "",
                    'Bot configuration happens through discord roles. A server admin can determine which roles are allowed to edit the bot\'s configuration using `/config permissions`. By default, all roles with the terms "game master" (or any variants thereof) will be allowed to configure the bot.',
                    "",
                    "Once the server admin is done allowing or disallowing specific roles, users with the allowed roles can then change the bot's behavior.",
                ],
            )
        ],
    )

    @property
    def tabs(self) -> list[HelpTab]:
        return [
            self.Overview,
            self.ContextMenus,
            self.Roll,
            self.Utility,
            self.Character,
            self.DND,
            self.Homebrew,
            self.Initiative,
            self.TokenGen,
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
        raise ValueError(f"help: tab '{tab}' not found.")


HelpTabs = HelpTabList()
