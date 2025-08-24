from itertools import product
import discord
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

from bot import Bot
from dnd import Gender
from utils.test_utils import listify
from commands.tokengen import AlignH, AlignV

img_url = r"https://img.lovepik.com/element/40116/9419.png_1200.png"


def mock_image() -> discord.Attachment:
    image = MagicMock(spec=discord.Attachment)
    image.url = img_url
    image.content_type = MagicMock()
    image.content_type = "image"
    return image


def mock_sound() -> discord.Attachment:
    sound = MagicMock(spec=discord.Attachment)
    sound.url = r"https://diviextended.com/wp-content/uploads/2021/10/sound-of-waves-marine-drive-mumbai.mp3"
    sound.content_type = MagicMock()
    sound.content_type = "audio"
    return sound


class TestBotCommands:
    @pytest.fixture()
    def bot(self):
        bot = Bot(voice=False)
        bot._register_commands()
        return bot

    @pytest.fixture()
    def commands(self, bot):
        return {cmd.name: cmd for cmd in bot.tree.get_commands()}

    @pytest_asyncio.fixture(autouse=True)
    def setup(self):
        self.mock_interaction = MagicMock(spec=discord.Interaction)
        self.mock_interaction.user = MagicMock(spec=discord.User)
        self.mock_interaction.user.id = (
            123456789  # Static user-id for commands that write user-data to files.
        )
        self.mock_interaction.user.display_name = "TestUser"
        self.mock_interaction.guild = MagicMock(spec=discord.Guild)
        self.mock_interaction.guild.id = 1234
        self.mock_interaction.channel = MagicMock(spec=discord.TextChannel)
        self.mock_interaction.response = MagicMock()
        self.mock_interaction.response.send_message = AsyncMock()
        self.mock_interaction.response.defer = AsyncMock()
        self.mock_interaction.followup = AsyncMock()

    def expand_arg_variants(self, arg: dict[str, any]) -> list[dict[str, any]]:
        """
        Iterates over the arguments and produces combinations when an argument is a list.
        """
        keys = list(arg.keys())
        values = [v if isinstance(v, list) else [v] for v in (arg[k] for k in keys)]
        combinations = product(*values)
        return [dict(zip(keys, combo)) for combo in combinations]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "cmd_name, arguments",
        [
            (
                "roll",
                {
                    "diceroll": ["1d20+6", "4d8kh3", "DiceExpression"],
                    "reason": [None, "Attack"],
                },
            ),
            ("d20", {}),
            (
                "advantage",
                {
                    "diceroll": ["1d20+6", "4d8kh3", "DiceExpression"],
                    "reason": [None, "Damage"],
                },
            ),
            (
                "disadvantage",
                {
                    "diceroll": ["1d20+6", "4d8kh3", "DiceExpression"],
                    "reason": [None, "Fire"],
                },
            ),
            ("shortcut", {}),
            ("spell", {"name": ["Fire Bolt", "abcdef"]}),
            ("item", {"name": ["Sword", "abcdef"]}),
            ("condition", {"name": ["Poisoned", "abcdef"]}),
            ("creature", {"name": ["Goblin", "abcdef"]}),
            ("class", {"name": ["Wizard", "abcdef"]}),
            ("rule", {"name": ["Action", "abcdef"]}),
            ("action", {"name": ["Attack", "abcdef"]}),
            ("feat", {"name": ["Tough", "abcdef"]}),
            ("language", {"name": ["Common", "abcdef"]}),
            ("background", {"name": ["Soldier", "abcdef"]}),
            ("table", {"name": ["Wild Magic", "abcdef"]}),
            ("species", {"name": ["Human", "abcdef"]}),
            (
                "search",
                [
                    {"query": "Barb"},
                    {"query": "qwertyuiopasdfghjkl;zxcvbnm,./1234567890"},
                ],
            ),
            (
                "namegen",
                {
                    "species": [None, "Human", "foobar"],
                    "gender": [
                        Gender.FEMALE.value,
                        Gender.MALE.value,
                        Gender.OTHER.value,
                    ],
                },
            ),
            (
                "color set hex",
                {"hex_color": ["#ff00ff", "ff00ff", "Not A color"]},
            ),
            (
                "color set rgb",
                {"r": [255, 0], "g": [255, 0], "b": [255, 0]},
            ),
            ("color show", {}),
            ("color clear", {}),  # Run clear last, to remove useless data from files.
            ("stats", {}),
            (
                "tokengen",
                [
                    {"image": mock_image()},
                    {"image": mock_image(), "frame_hue": [-180, 0, 180]},
                    {
                        "image": mock_image(),
                        "h_alignment": [
                            AlignH.RIGHT.value,
                            AlignH.CENTER.value,
                            AlignH.LEFT.value,
                        ],
                    },
                    {
                        "image": mock_image(),
                        "v_alignment": [
                            AlignV.BOTTOM.value,
                            AlignV.CENTER.value,
                            AlignV.TOP.value,
                        ],
                    },
                    {"image": mock_image(), "variants": [0, 3, 10]},
                ],
            ),
            (
                "tokengenurl",
                [
                    {"url": img_url},
                    {"url": img_url, "frame_hue": [-180, 0, 180]},
                    {
                        "url": img_url,
                        "h_alignment": [
                            AlignH.RIGHT.value,
                            AlignH.CENTER.value,
                            AlignH.LEFT.value,
                        ],
                    },
                    {
                        "url": img_url,
                        "v_alignment": [
                            AlignV.BOTTOM.value,
                            AlignV.CENTER.value,
                            AlignV.TOP.value,
                        ],
                    },
                    {"url": img_url, "variants": [0, 3, 10]},
                    {"url": "NotAUrl"},
                ],
            ),
            ("initiative", {}),
            (
                "plansession",
                {"in_weeks": [0, 1, 4], "poll_duration": [1, 24, 168]},
            ),
            (
                "playsound",
                {"sound": [mock_sound(), mock_image()]},
            ),
            ("help", {}),
            # ("", {"": "", "": ""}),
        ],
    )
    async def test_slash_commands(
        self,
        commands: list[discord.app_commands.Command],
        cmd_name: str,
        arguments: dict | list[dict],
    ):
        def get_cmd_from_group(
            group: discord.app_commands.Group, parts: list[str]
        ) -> discord.app_commands.Command:
            """Recursively looks for a command within command-groups."""
            cmd = group.get_command(parts[0])
            if isinstance(cmd, discord.app_commands.Group):
                return get_cmd_from_group(cmd, parts[1:])
            return cmd

        if " " in cmd_name:
            # Only groups can have spaces in the name
            parts = [p.strip() for p in cmd_name.split(" ")]
            root = commands.get(parts[0])
            cmd = get_cmd_from_group(root, parts[1:])
        else:
            cmd = commands.get(cmd_name)

        assert cmd is not None, f"{cmd_name} command not found"

        arguments = listify(arguments)

        for arg_set in arguments:
            arg_variants = self.expand_arg_variants(arg_set)
            for args in arg_variants:
                try:
                    await cmd.callback(itr=self.mock_interaction, **args)
                except Exception as e:
                    pytest.fail(
                        f"Error while running command /{cmd_name} with args {args}: {e}"
                    )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "cmd_name, param_name, queries",
        [
            ("roll", "diceroll", ["", "1d20"]),
            ("advantage", "diceroll", ["", "1d20"]),
            ("disadvantage", "diceroll", ["", "1d20"]),
            ("roll", "reason", ["", "Att"]),
            ("advantage", "reason", ["", "Dam"]),
            ("disadvantage", "reason", ["", "Ste"]),
            ("spell", "name", ["", "Fireb"]),
            ("item", "name", ["", "Dag"]),
            ("condition", "name", ["", "Poi"]),
            ("creature", "name", ["", "Gobl"]),
            ("class", "name", ["", "Bar"]),
            ("rule", "name", ["", "Adv"]),
            ("action", "name", ["", "Att"]),
            ("feat", "name", ["", "Tou"]),
            ("language", "name", ["", "Comm"]),
            # ('', '', ''),
        ],
    )
    async def test_autocomplete_suggestions(
        self,
        commands: list[discord.app_commands.Command],
        cmd_name: str,
        param_name: str,
        queries: str | list[str],
    ):
        cmd = commands.get(cmd_name)
        assert cmd is not None, f"Command {cmd_name} not found"

        param = cmd._params.get(param_name)
        assert (
            param is not None
        ), f"Parameter '{param_name}' not found in command '{cmd_name}'"

        autocomplete_fn = param.autocomplete
        assert (
            autocomplete_fn is not None
        ), f"No autocomplete function set for parameter '{param_name}' in {cmd_name}"
        assert not isinstance(
            autocomplete_fn, bool
        ), f"No autocomplete function set for parameter '{param_name}' in {cmd_name}"

        queries = listify(queries)

        for current in queries:
            try:
                await autocomplete_fn(cmd, self.mock_interaction, current)
            except Exception as e:
                pytest.fail(
                    f"Error while autocompleting '{param_name}' for /{cmd_name} with query '{current}': {e}"
                )
