from itertools import product
import discord
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

from bot import Bot
from logic.dnd.data import Data
from logic.dnd.name import Gender
from logic.roll import Advantage
from utils.mocking import mock_image, mock_sound
from utils.test_utils import enum_values, listify
from commands.tokengen import AlignH, AlignV


def get_cmd_from_group(group: discord.app_commands.Group, parts: list[str]) -> discord.app_commands.Command:
    """Recursively looks for a command within command-groups."""
    cmd = group.get_command(parts[0])
    if isinstance(cmd, discord.app_commands.Group):
        return get_cmd_from_group(cmd, parts[1:])
    return cmd


def get_cmd(
    commands: dict[
        str,
        discord.app_commands.Command | discord.app_commands.ContextMenu | discord.app_commands.Group,
    ],
    name: str,
):
    if " " in name:
        # Only groups can have spaces in the name
        parts = [p.strip() for p in name.split(" ")]
        root = commands.get(parts[0])
        return get_cmd_from_group(root, parts[1:])
    else:
        return commands.get(name)


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
        self.mock_interaction.user.id = 123456789  # Static user-id for commands that write user-data to files.
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
                    "diceroll": ["1d20+6", "4d8kh3", "1d8ro1"],
                    "reason": [None, "Attack"],
                },
            ),
            ("d20", {}),
            (
                "advantage",
                {
                    "diceroll": ["1d20+6", "4d8kh3", "1d8ro1"],
                    "reason": [None, "Damage"],
                },
            ),
            (
                "disadvantage",
                {
                    "diceroll": ["1d20+6", "4d8kh3", "1d8ro1"],
                    "reason": [None, "Fire"],
                },
            ),
            ("search spell", {"name": ["Fire Bolt", "abcdef"]}),
            ("search item", {"name": ["Sword", "abcdef"]}),
            ("search condition", {"name": ["Poisoned", "abcdef"]}),
            ("search creature", {"name": ["Goblin", "abcdef"]}),
            (
                "search class",
                {"name": ["Wizard", "Fighter", "abcdef"]},
            ),  # Search spellcaster & non spellcaster classes, since they render differently
            ("search rule", {"name": ["Action", "abcdef"]}),
            ("search action", {"name": ["Attack", "abcdef"]}),
            ("search feat", {"name": ["Tough", "abcdef"]}),
            ("search language", {"name": ["Common", "abcdef"]}),
            ("search background", {"name": ["Soldier", "abcdef"]}),
            ("search table", {"name": ["Wild Magic", "abcdef"]}),
            ("search species", {"name": ["Human", "abcdef"]}),
            (
                "search all",
                [
                    {
                        "query": [
                            "Barb",
                            "Sailor",
                            "qwertyuiopasdfghjkl;zxcvbnm,./1234567890",
                        ]
                    },  # Sailor can give problematic results, ensure this does not re-occur.
                ],
            ),
            (
                "namegen",
                {
                    "species": [None, "foobar"].extend([spec.title() for spec in Data.names.get_species()]),
                    "gender": enum_values(Gender),
                },
            ),
            (
                "color set hex",
                {"hex_color": ["#ff00ff", "ff00ff"]},
            ),
            (
                "color set rgb",
                {"r": [255, 0], "g": [255, 0], "b": [255, 0]},
            ),
            ("color show", {}),
            ("color clear", {}),  # Run clear last, to remove useless data from files.
            ("stats roll", {}),
            (
                "stats visualise",
                {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
            ),
            (
                "tokengen file",
                [
                    {"image": mock_image()},
                    {"image": mock_image(), "frame_hue": [-180, 0, 180]},
                    {
                        "image": mock_image(),
                        "h_alignment": enum_values(AlignH),
                    },
                    {
                        "image": mock_image(),
                        "v_alignment": enum_values(AlignV),
                    },
                    {"image": mock_image(), "variants": [0, 3, 10]},
                ],
            ),
            (
                "tokengen url",
                [
                    {"url": mock_image().url},
                    {"url": mock_image().url, "frame_hue": [-180, 0, 180]},
                    {
                        "url": mock_image().url,
                        "h_alignment": enum_values(AlignH),
                    },
                    {
                        "url": mock_image().url,
                        "v_alignment": enum_values(AlignV),
                    },
                    {"url": mock_image().url, "variants": [0, 3, 10]},
                ],
            ),
            ("initiative", {}),
            (
                "plansession",
                {"in_weeks": [0, 1, 4], "poll_duration": [1, 24, 168]},
            ),
            ("help", {}),
            (
                "timestamp relative",
                {
                    "seconds": [0, 30],
                    "minutes": [0, 30],
                    "hours": [0, 12],
                    "days": [0, 5],
                    "weeks": [0, 4],
                },
            ),
            (
                "timestamp date",
                [
                    {
                        "time": ["1838", "7:40", "5", "18"],
                        "timezone": [2, -6],
                        "date": [
                            None,
                            "05/03/2025",
                            "05/03",
                            "05.03.2025",
                            "05.03",
                            "5",
                        ],
                    },
                ],
            ),
            (
                "distribution",
                {
                    "expression": ["1d20", "1d8ro1"],
                    "advantage": enum_values(Advantage),
                    "min_to_beat": [None, "5"],
                },
            ),
            ("charactergen", {}),
            # ("", {"": "", "": ""}),
        ],
    )
    async def test_slash_commands(
        self,
        commands: list[discord.app_commands.Command],
        cmd_name: str,
        arguments: dict | list[dict],
    ):
        cmd = get_cmd(commands, cmd_name)
        assert cmd is not None, f"{cmd_name} command not found"

        arguments = listify(arguments)

        for arg_set in arguments:
            arg_variants = self.expand_arg_variants(arg_set)
            for args in arg_variants:
                try:
                    await cmd.callback(itr=self.mock_interaction, **args)
                except Exception as e:
                    pytest.fail(f"Error while running command /{cmd_name} with args {args}: {e}")

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "cmd_name, arguments",
        [
            (
                "roll",
                {
                    "diceroll": ["DiceExpression"],
                    "reason": None,
                },
            ),
            (
                "advantage",
                {
                    "diceroll": "DiceExpression",
                    "reason": None,
                },
            ),
            (
                "disadvantage",
                {
                    "diceroll": "DiceExpression",
                    "reason": None,
                },
            ),
            (
                "timestamp date",
                [
                    {"time": "Wrong", "timezone": 0},
                    {"time": "1830", "timezone": 0, "date": ["Wrong", "32", "05/13"]},
                ],
            ),
            (
                "color set hex",
                {"hex_color": "Green"},
            ),
            (
                "playsound",
                {"sound": [mock_sound(), mock_image()]},
            ),
            (
                "tokengen file",
                [
                    {"image": mock_sound()},
                ],
            ),
            (
                "tokengen url",
                [
                    {"url": "NotAUrl"},
                ],
            ),
            # ("", {"": "", "": ""}),
        ],
    )
    async def test_slash_commands_expecting_failure(
        self,
        commands: list[discord.app_commands.Command],
        cmd_name: str,
        arguments: dict | list[dict],
    ):
        # This is the same test as test_slash_commands, except
        # we expect errors to be thrown
        cmd = get_cmd(commands, cmd_name)
        assert cmd is not None, f"{cmd_name} command not found"

        arguments = listify(arguments)

        for arg_set in arguments:
            arg_variants = self.expand_arg_variants(arg_set)
            for args in arg_variants:
                with pytest.raises(Exception):
                    await cmd.callback(itr=self.mock_interaction, **args)

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
            ("search spell", "name", ["", "Fireb"]),
            ("search item", "name", ["", "Dag"]),
            ("search condition", "name", ["", "Poi"]),
            ("search creature", "name", ["", "Gobl"]),
            ("search class", "name", ["", "Bar"]),
            ("search rule", "name", ["", "Adv"]),
            ("search action", "name", ["", "Att"]),
            ("search feat", "name", ["", "Tou"]),
            ("search language", "name", ["", "Comm"]),
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
        cmd = get_cmd(commands, cmd_name)
        assert cmd is not None, f"Command {cmd_name} not found"

        param = cmd._params.get(param_name)
        assert param is not None, f"Parameter '{param_name}' not found in command '{cmd_name}'"

        autocomplete_fn = param.autocomplete
        assert autocomplete_fn is not None, f"No autocomplete function set for parameter '{param_name}' in {cmd_name}"
        assert not isinstance(autocomplete_fn, bool), f"No autocomplete function set for parameter '{param_name}' in {cmd_name}"

        queries = listify(queries)

        for current in queries:
            try:
                await autocomplete_fn(cmd, self.mock_interaction, current)
            except Exception as e:
                pytest.fail(f"Error while autocompleting '{param_name}' for /{cmd_name} with query '{current}': {e}")
