from enum import Enum

from embeds import SimpleEmbed


class HelpTabs(Enum):
    Default = "General"
    Roll = "Rolling Dice"
    Initiative = "Initiative Tracking"
    DND = "D&D Info Lookup"
    TokenGen = "Token Generation"
    Color = "User Color"
    Stats = "Character Stats"


class FieldInfo:
    def __init__(self, name: HelpTabs, description: list[str]):
        self.name = name
        self._descriptions = description

    @property
    def description(self) -> str:
        return "\n".join(self._descriptions)


def _get_default_help_inline_fields() -> list[FieldInfo]:
    """
    Returns a list of FieldInfo with each command per category, to be rendered with inline = True.
    This is only displayed on the general help tab.
    """
    fields = [
        FieldInfo(
            name=HelpTabs.Roll.value,
            description=[
                "- ``/roll``",
                "- ``/advantage``",
                "- ``/disadvantage``",
                "- ``/d20``",
            ],
        ),
        FieldInfo(
            name=HelpTabs.Initiative.value,
            description=[
                "- ``/initiative``",
                "- ``/bulkinitiative``",
                "- ``/setinitiative``",
                "- ``/swapinitiative``",
                "- ``/removeinitiative``",
                "- ``/showinitiative``",
                "- ``/clearinitiative``",
            ],
        ),
        FieldInfo(
            name=HelpTabs.DND.value,
            description=[
                "- ``/spell``",
                "- ``/item``",
                "- ``/condition``",
                "- ``/creature``",
                "- ``/feat``",
                "- ``/rule``",
                "- ``/action``",
                "- ``/search``",
            ],
        ),
        FieldInfo(
            name=HelpTabs.TokenGen.value,
            description=[
                "- ``/tokengen``",
                "- ``/tokengenurl``",
            ],
        ),
        FieldInfo(
            name=HelpTabs.Color.value,
            description=[
                "- ``/color``",
            ],
        ),
        FieldInfo(
            name=HelpTabs.Stats.value,
            description=[
                "- ``/stats``",
            ],
        ),
    ]

    return sorted(fields, key=lambda f: len(f._descriptions), reverse=True)


def _get_help_fields(tab: HelpTabs) -> tuple[str, FieldInfo]:
    """Returns the help text for a specific tab, to be rendered with inline = False."""
    match tab:
        case HelpTabs.Roll:
            return "Rolling Dice", [
                FieldInfo(
                    name="Commands",
                    description=[
                        "You can roll dice using the following commands:",
                        "- ``/roll <dice notation> [reason]`` - Roll a single dice expression.",
                        "- ``/advantage <dice notation> [reason]`` - Roll the expression twice, use the highest result.",
                        "- ``/disadvantage <dice notation> [reason]`` - Roll the expression twice, use the lowest result.",
                        "- ``/d20`` - Rolls a basic 1d20 with no modifiers.",
                    ],
                ),
                FieldInfo(
                    name="Using Dice Notations",
                    description=[
                        "To roll dice, you need to use dice notations, these follow the format `XdY + Z`.",
                        "For example, ``1d20 + 6`` rolls a single 20-sided die and adds 6 to the result, these notations are expandable to combine a large number of dice.",
                        "Besides basic math operators (``+``, ``-``, ``/``, ``*``), ``NdN`` and numbers, you can also use modifiers [documented on this site.](https://d20.readthedocs.io/en/latest/start.html#grammar)",
                    ],
                ),
                FieldInfo(
                    name="Sound effects",
                    description=[
                        "If FFMPEG is installed, the bot will play sound effects for rolls, by default these are basic dice-rolling sounds.",
                        "A handful of reasons or events may trigger a special sound effect, these are the following:",
                        "- *Critical Hit* - When a 1d20 results to 20, a critical hit sound is played.",
                        "- *Critical Fail* - When a 1d20 results to 1, a critical fail sound is played.",
                        "- *Attack* - If the specified rason is `attack`, an attack sound is played.",
                        "- *Damage* - If the specified reason is `damage`, a damage sound is played.",
                        "- *Fire* - If the specified reason is `fire`, a fire sound is played.",
                    ],
                ),
            ]
        case HelpTabs.Initiative:
            return "Initiative Tracking", [
                FieldInfo(
                    name="Commands",
                    description=[
                        "You can track initiatives for combat using the following commands,",
                        "- ``/initiative <modifier> [target] [roll_mode]`` - Rolls for initiative.",
                        "- ``/bulkinitiative <modifier> <name> <amount> [roll_mode] [shared]`` - Rolls initiative for multiple targets at once.",
                        "- ``/setinitiative <value> [name]`` - Sets a specific initiative value for a target.",
                        "- ``/swapinitiative <target a> <target b>`` - Swap initiatives between two targets.",
                        "- ``/removeinitiative [target]`` - Removes a single creature from the tracker."
                        "- ``/showinitiative`` - Shows an embed with all the initiatives, used to track the order & who's turn it is.",
                        "- ``/clearinitiative`` - Clears all stored initiatives in the server, used after a battle.",
                    ],
                ),
                FieldInfo(
                    name="Initiative Settings",
                    description=[
                        "By default, names are enforced to be unique and will overwrite existing targets.",
                        "Some of these commands have a lot of options, here is an overview of the meaning of optional options:",
                        "- ``target`` - Used to roll initiative for NPC's / Creatures. If not specified it defaults to the user.",
                        "- ``roll_mode`` - Used to specify the roll mode, this can be `normal`, `advantage`, or `disadvantage`.",
                        "- ``shared`` - Used to use the same initiative value for all creatures in the bulk-roll.",
                    ],
                ),
            ]
        case HelpTabs.DND:
            return "DND Data Lookup", [
                FieldInfo(
                    name="Commands",
                    description=[
                        "Dungeons & Dragons is a game with a lot of information, you can easily look up information from [5e.tools](https://5e.tools/) using the following commands:",
                        "- ``/spell <spell-name>`` - Looks up a spell by name.",
                        "- ``/item <item-name>`` - Look up an item by name.",
                        "- ``/condition <condition-name>`` - Looks up a condition/ailment by name.",
                        "- ``/creature <creature-name>`` - Looks up a creature by name.",
                        "- ``/rule <rule-name>`` - Looks up a rule by name.",
                        "- ``/action <action-name>`` - Looks up an action by name.",
                        "- ``/search <query>`` - Searches for matching results across all categories.",
                    ],
                )
            ]
        case HelpTabs.TokenGen:
            return "Token-Image Generation", [
                FieldInfo(
                    name="Commands",
                    description=[
                        "You can generate token images for your characters or creatures in the 5e.tools style using the following commands:",
                        "- ``/tokengen <image-attachment> [hue-shift] [h_alignment] [v_alignment]`` - Generates a token image from an image attachment.",
                        "- ``/tokengenurl <image-url> [hue-shift] [h_alignment] [v_alignment]`` - Generates a token image from an image-URL.",
                    ],
                ),
                FieldInfo(
                    name="Image Adjustment",
                    description=[
                        "There are a few options to adjust the way a token image is generated, by default it will provide a golden border and center the provided image.",
                        "However you can use the following options to adjust the way the token is generated:",
                        "- ``hue-shift`` - Allows you to shift the color of the token's border, this is a number between -360 and 360. By default a shift of 0 is used, which results in a golden border.",
                        "- ``h_alignment`` - Adjusts the horizontal alignment of the image, this can be `left`, `center`, or `right`.",
                        "- ``v_alignment`` - Adjusts the vertical alignment of the image, this can be `top`, `center`, or `bottom`.",
                    ],
                ),
            ]
        case HelpTabs.Color:
            return "User Colors", [
                FieldInfo(
                    name="",
                    description=[
                        "Commands that signify user-actions (/roll, /initiative, ...) will have a special embed-color, to easily discern different actions from different users.",
                        "By default, a random color is generated depending on the user's display name, however you can set a custom color using the following commands:",
                        "- ``/color [hex-value]`` - Set a custom color for yourself by providing a hex value.",
                        "- ``/color`` - Using the command without a hex-value defaults the user's color back to an auto-generated one.",
                    ],
                )
            ]
        case HelpTabs.Stats:
            return "Character Stats", [
                FieldInfo(
                    name="",
                    description=[
                        "You can easily generate stats for your character using the following command:",
                        "- ``/stats`` - Rolls 6 dice using the 4d6 drop lowest method, providing you with 6 distint values to use for your new character.",
                    ],
                )
            ]
        case _:
            return "General", [
                FieldInfo(
                    name="",
                    description=[
                        "You can view more detailed information regarding command-groups by using ``/help <tab>``. The following tabs are available:",
                        "\n".join([f"- ``{tab.value}``" for tab in HelpTabs]),
                    ],
                ),
            ]


def get_help_embed(tab: HelpTabs) -> SimpleEmbed:
    """Generates a help embed depending on the selected tab."""
    title, field_info = _get_help_fields(tab)

    embed = SimpleEmbed(
        title=f"Help - {title}",
        description="",
    )

    if tab == HelpTabs.Default:
        embed.description = "This bot provides a wide range of handy 5th edition Dungeon & Dragons commands, to help you with your games."
        for info in _get_default_help_inline_fields():
            embed.add_field(name=info.name, value=info.description, inline=True)

    else:
        for info in field_info:
            embed.add_field(name=info.name, value=info.description, inline=False)

    return embed
