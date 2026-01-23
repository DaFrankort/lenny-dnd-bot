from itertools import product
from typing import Any, Iterable, TypeVar

import pytest

# Required to mark the library as essential for testing in our workflows
import pytest_asyncio  # noqa: F401 # type: ignore
from utils.mocking import (
    MockDirectMessageInteraction,
    MockImage,
    MockInteraction,
    MockSound,
)
from utils.utils import listify

from bot import Bot
from commands.command import BaseCommand, BaseCommandGroup
from commands.tokengen import AlignH, AlignV
from embeds.dnd.class_ import ClassEmbed
from logic.charactergen import class_choices, species_choices
from logic.color import BasicColors
from logic.config import Config, ConfigHandler
from logic.dnd.abstract import DNDEntry, DNDEntryList
from logic.dnd.data import Data
from logic.dnd.name import Gender
from logic.roll import Advantage
from logic.tokengen import BackgroundType

SLASH_COMMAND_TESTS: Iterable[Iterable[Any]] = [
    (
        "roll",
        {
            "diceroll": ["1d20+6", "4d8kh3", "1d8ro1", "1>0", "1<0", "(1d20+7>14) * 1d8"],
            "reason": [None, "Attack", "Fire"],
            "advantage": [None, "normal", "advantage", "disadvantage"],
        },
    ),
    ("d20", {}),
    (
        "multiroll",
        {
            "diceroll": ["1d20+6", "4d8kh3", "1d8ro1", "1>0", "1<0", "(1d20+7>14) * 1d8"],
            "amount": [1, 3],
            "advantage": Advantage.values(),
            "reason": [None, "Attack"],
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
    ("search deity", {"name": ["Arawai", "Anubis", "abcdef"]}),
    ("search feat", {"name": ["Tough", "abcdef"]}),
    ("search language", {"name": ["Common", "abcdef"]}),
    ("search background", {"name": ["Soldier", "abcdef"]}),
    ("search table", {"name": ["Wild Magic", "abcdef"]}),
    ("search species", {"name": ["Human", "abcdef"]}),
    ("search vehicle", {"name": ["Galley", "abcdef"]}),
    ("search object", {"name": ["Ballista", "abcdef"]}),
    ("search hazard", {"name": ["Spiked Pit", "abcdef"]}),
    ("search cult", {"name": ["Cult of Dispater", "abcdef"]}),
    ("search boon", {"name": ["Demonic Boon of Balor", "abcdef"]}),
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
            "gender": Gender.values(),
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
    (
        "color set base",
        {"color": [BasicColors.RED.value, BasicColors.BLUE.value, BasicColors.GREEN.value]},
    ),
    ("color show", {}),
    ("color clear", {}),  # Run clear last, to remove useless data from files.
    ("stats roll", {}),
    (
        "stats visualize",
        {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
    ),
    (
        "tokengen file",
        [
            {"image": MockImage()},
            {"image": MockImage(), "frame_hue": [-180, 0, 180]},
            {"image": MockImage(), "h_alignment": AlignH.values()},
            {"image": MockImage(), "v_alignment": AlignV.values()},
            {"image": MockImage(), "variants": [0, 3, 10]},
            {"image": MockImage(), "background_type": BackgroundType.values()},
        ],
    ),
    (
        "tokengen url",
        [
            {"url": MockImage().url},
            {"url": MockImage().url, "frame_hue": [-180, 0, 180]},
            {"url": MockImage().url, "h_alignment": AlignH.values()},
            {"url": MockImage().url, "v_alignment": AlignV.values()},
            {"url": MockImage().url, "variants": [0, 3, 10]},
            {"url": MockImage().url, "background_type": BackgroundType.values()},
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
    ("distribution", {"expression": ["1d20", "1d8ro1"], "advantage": Advantage.values(), "min_to_beat": [None, "5"]}),
    (
        "charactergen",
        {
            "gender": [None, Gender.FEMALE],
            "species": [None, "human"],
            "char_class": [None, "rogue"],
        },
    ),
    # Homebrew commands work through modals, and are thus not testable.
    # ("", {"": "", "": ""}),
]


def get_cmd_from_group(group: BaseCommandGroup, parts: list[str]) -> BaseCommand | None:
    """Recursively looks for a command within command-groups."""
    if len(parts) == 0:
        return None

    cmd = group.get_command(parts[0])
    if not isinstance(cmd, (BaseCommand, BaseCommandGroup)):
        raise ValueError("All commands in a SimpleCommandGroup should either be SimpleCommandGroups or SimpleCommands")
    if isinstance(cmd, BaseCommandGroup):
        return get_cmd_from_group(cmd, parts[1:])
    return cmd


def get_cmd(commands: dict[str, BaseCommand | BaseCommandGroup], name: str) -> BaseCommand | None:
    name = name.strip()
    if not name:
        return None

    names = [n.strip() for n in name.split(" ")]
    name = names[0]
    rest = names[1:]

    command = commands.get(name, None)
    if isinstance(command, BaseCommandGroup):
        return get_cmd_from_group(command, rest)
    else:
        return command


TEntry = TypeVar("TEntry", bound=DNDEntry)


def get_strict_search_arguments(entry_list: DNDEntryList[TEntry]) -> list[str]:
    disallowed_sources = ConfigHandler.default_disallowed_sources()
    return [entry.name for entry in entry_list.entries if entry.source not in disallowed_sources]


class TestBotCommands:
    @pytest.fixture()
    def bot(self):
        try:
            bot = Bot(voice=False)

            bot.register_commands()
        except Exception:
            pytest.fail("Bot could not be launched!")
        return bot

    @pytest.fixture()
    def commands(self, bot: Bot) -> dict[str, BaseCommand | BaseCommandGroup]:
        return {cmd.name: cmd for cmd in bot.tree.get_commands() if isinstance(cmd, (BaseCommand, BaseCommandGroup))}

    def expand_arg_variants(self, arg: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Iterates over the arguments and produces combinations when an argument is a list.
        """
        keys = list(arg.keys())
        values: list[list[Any]] = [v if isinstance(v, list) else [v] for v in (arg[k] for k in keys)]
        combinations = product(*values)
        return [dict(zip(keys, combo)) for combo in combinations]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("cmd_name, arguments", SLASH_COMMAND_TESTS)
    @pytest.mark.timeout(60)  # Protect against infinite loops
    async def test_slash_commands_guild(
        self,
        commands: dict[str, BaseCommand | BaseCommandGroup],
        cmd_name: str,
        arguments: dict[str, Any] | list[dict[str, Any]],
    ):
        itr = MockInteraction()
        cmd = get_cmd(commands, cmd_name)
        assert cmd is not None, f"{cmd_name} command not found"

        arguments = listify(arguments)

        for arg_set in arguments:
            arg_variants = self.expand_arg_variants(arg_set)
            for args in arg_variants:
                try:
                    await cmd.handle(itr=itr, **args)
                except Exception as e:
                    pytest.fail(f"Error while running command /{cmd_name} in GUILD with args {args}: {e}")

    @pytest.mark.strict
    @pytest.mark.asyncio
    @pytest.mark.parametrize("cmd_name, arguments", SLASH_COMMAND_TESTS)
    @pytest.mark.timeout(60)  # Protect against infinite loops
    async def test_slash_commands_private_message(
        self,
        commands: dict[str, BaseCommand | BaseCommandGroup],
        cmd_name: str,
        arguments: dict[str, Any] | list[dict[str, Any]],
    ):
        itr = MockDirectMessageInteraction()
        cmd = get_cmd(commands, cmd_name)
        assert cmd is not None, f"{cmd_name} command not found"

        if cmd.guild_only:
            pytest.skip(reason=f"{cmd_name} is a guild-only command, skipping.")

        arguments = listify(arguments)

        for arg_set in arguments:
            arg_variants = self.expand_arg_variants(arg_set)
            for args in arg_variants:
                try:
                    await cmd.handle(itr=itr, **args)
                except Exception as e:
                    pytest.fail(f"Error while running command /{cmd_name} in PRIVATE MESSAGE with args {args}: {e}")

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
                "roll",
                {
                    "diceroll": ["1d20"],
                    "reason": None,
                    "advantage": "invalid",
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
                {"sound": [MockSound(), MockImage()]},
            ),
            (
                "tokengen file",
                [
                    {"image": MockSound()},
                    {"image": MockImage(has_face=False), "h_alignment": AlignH.FACE, "v_alignment": AlignV.FACE},
                ],
            ),
            (
                "tokengen url",
                [
                    {"url": "NotAUrl"},
                    {"image": MockImage(has_face=False).url, "h_alignment": AlignH.FACE, "v_alignment": AlignV.FACE},
                ],
            ),
            # ("", {"": "", "": ""}),
        ],
    )
    async def test_slash_commands_expecting_failure(
        self,
        commands: dict[str, BaseCommand | BaseCommandGroup],
        cmd_name: str,
        arguments: dict[str, Any] | list[dict[str, Any]],
    ):
        itr = MockInteraction()
        # This is the same test as test_slash_commands, except
        # we expect errors to be thrown
        cmd = get_cmd(commands, cmd_name)
        assert cmd is not None, f"{cmd_name} command not found"

        arguments = listify(arguments)

        for arg_set in arguments:
            arg_variants = self.expand_arg_variants(arg_set)
            for args in arg_variants:
                with pytest.raises(Exception):
                    await cmd.handle(itr=itr, **args)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "cmd_name, param_name, queries",
        [
            ("roll", "diceroll", ["", "1d20"]),
            ("multiroll", "diceroll", ["", "1d20"]),
            ("roll", "reason", ["", "Att"]),
            ("multiroll", "reason", ["", "Att"]),
            ("search spell", "name", ["", "Fireb"]),
            ("search item", "name", ["", "Dag"]),
            ("search condition", "name", ["", "Poi"]),
            ("search creature", "name", ["", "Gobl"]),
            ("search class", "name", ["", "Bar"]),
            ("search rule", "name", ["", "Adv"]),
            ("search action", "name", ["", "Att"]),
            ("search feat", "name", ["", "Tou"]),
            ("search language", "name", ["", "Comm"]),
            ("search background", "name", ["", "Sail"]),
            ("search table", "name", ["", "Wild"]),
            ("search species", "name", ["", "Hum"]),
            ("search vehicle", "name", ["", "Shi"]),
            ("search object", "name", ["", "Can"]),
            ("search hazard", "name", ["", "Spi"]),
            ("search deity", "name", ["", "Anu"]),
            ("search cult", "name", ["", "Cult of Dispa"]),
            ("search boon", "name", ["", "Demonic Boon of Bal"]),
            # ('', '', ''),
        ],
    )
    async def test_autocomplete_suggestions(
        self,
        commands: dict[str, BaseCommand | BaseCommandGroup],
        cmd_name: str,
        param_name: str,
        queries: str | list[str],
    ):
        itr = MockInteraction()
        cmd = get_cmd(commands, cmd_name)
        assert cmd is not None, f"Command {cmd_name} not found"

        param = cmd.params.get(param_name)

        assert param is not None, f"Parameter '{param_name}' not found in command '{cmd_name}'"
        assert param.autocomplete is not None, f"No autocomplete function set for parameter '{param_name}' in {cmd_name}"

        queries = listify(queries)

        for current in queries:
            try:
                await param.autocomplete(itr, current)
            except Exception as e:
                pytest.fail(f"Error while autocompleting '{param_name}' for /{cmd_name} with query '{current}': {e}")

    @pytest.mark.strict
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "cmd_name, arguments",
        [
            ("search spell", {"name": get_strict_search_arguments(Data.spells)}),
            ("search item", {"name": get_strict_search_arguments(Data.items)}),
            ("search condition", {"name": get_strict_search_arguments(Data.conditions)}),
            ("search creature", {"name": get_strict_search_arguments(Data.creatures)}),
            (
                "search class",
                {"name": get_strict_search_arguments(Data.classes)},
            ),
            ("search rule", {"name": get_strict_search_arguments(Data.rules)}),
            ("search action", {"name": get_strict_search_arguments(Data.actions)}),
            ("search deity", {"name": get_strict_search_arguments(Data.deities)}),
            ("search feat", {"name": get_strict_search_arguments(Data.feats)}),
            ("search language", {"name": get_strict_search_arguments(Data.languages)}),
            ("search background", {"name": get_strict_search_arguments(Data.backgrounds)}),
            ("search table", {"name": get_strict_search_arguments(Data.tables)}),
            ("search species", {"name": get_strict_search_arguments(Data.species)}),
            ("search vehicle", {"name": get_strict_search_arguments(Data.vehicles)}),
            ("search object", {"name": get_strict_search_arguments(Data.objects)}),
            ("search hazard", {"name": get_strict_search_arguments(Data.hazards)}),
            ("search boon", {"name": get_strict_search_arguments(Data.boons)}),
            (
                "charactergen",
                {
                    "gender": Gender.values(),
                    "species": [species.value for species in species_choices()],
                    "char_class": [class_.value for class_ in class_choices()],
                },
            ),
            ("namegen", {"species": [spec.title() for spec in Data.names.get_species()], "gender": Gender.values()}),
        ],
    )
    async def test_slash_strict(
        self,
        commands: dict[str, BaseCommand | BaseCommandGroup],
        cmd_name: str,
        arguments: dict[str, Any] | list[dict[str, Any]],
    ):
        itr = MockInteraction()
        cmd = get_cmd(commands, cmd_name)
        assert cmd is not None, f"{cmd_name} command not found"

        arguments = listify(arguments)
        failures: list[tuple[dict[str, Any], str]] = []

        for arg_set in arguments:
            arg_variants = self.expand_arg_variants(arg_set)
            for args in arg_variants:
                try:
                    await cmd.handle(itr=itr, **args)
                except Exception as e:
                    failures.append((args, str(e)))

        if failures:
            failure_messages = "\n".join([f"Args: {args}, Error: {error}" for args, error in failures])
            pytest.fail(f"Errors while running command /{cmd_name}:\n{failure_messages}")

    @pytest.mark.strict
    async def test_class_strict(self):
        """Tests the class embeds for all classes and subclasses at all levels"""
        itr = MockInteraction()
        sources = Config.get(itr).all_sources
        sources = set(source.id for source in sources)

        classes = Data.classes
        levels = list(range(0, 21))

        for class_ in classes.entries:
            subclass = class_.subclasses
            for subclass in [None, *class_.subclasses]:
                for level in levels:
                    embed = ClassEmbed(class_, set(sources), level, subclass)
                    assert embed.view is not None
