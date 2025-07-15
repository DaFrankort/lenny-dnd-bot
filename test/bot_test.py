from itertools import product
import discord
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

from bot import Bot
import i18n
from i18n import t
from token_gen import AlignH, AlignV

i18n.set_locale("./assets/locales/en.json")
img_url = r"https://img.lovepik.com/element/40116/9419.png_1200.png"


def mock_image() -> discord.Attachment:
    image = MagicMock(spec=discord.Attachment)
    image.url = img_url
    image.content_type = MagicMock()
    image.content_type = "image"
    return image


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
                t("commands.roll.name"),
                {
                    "diceroll": ["1d20+6", "4d8kh3", "DiceExpression"],
                    "reason": [None, "Attack"],
                },
            ),
            (t("commands.d20.name"), {}),
            (
                t("commands.advantage.name"),
                {
                    "diceroll": ["1d20+6", "4d8kh3", "DiceExpression"],
                    "reason": [None, "Damage"],
                },
            ),
            (
                t("commands.disadvantage.name"),
                {
                    "diceroll": ["1d20+6", "4d8kh3", "DiceExpression"],
                    "reason": [None, "Fire"],
                },
            ),
            (t("commands.shortcut.name"), {}),
            (t("commands.spell.name"), [{"name": "Fire Bolt"}, {"name": "abcdefg"}]),
            (t("commands.item.name"), [{"name": "Sword"}, {"name": "abcdefg"}]),
            (t("commands.condition.name"), [{"name": "Poisoned"}, {"name": "abcdefg"}]),
            (t("commands.creature.name"), [{"name": "Goblin"}, {"name": "abcdef"}]),
            (t("commands.class.name"), [{"name": "Wizard"}, {"name": "abcdef"}]),
            (t("commands.rule.name"), [{"name": "Action"}, {"name": "abcdef"}]),
            (t("commands.action.name"), [{"name": "Attack"}, {"name": "abcdef"}]),
            (t("commands.feat.name"), [{"name": "Tough"}, {"name": "abcdef"}]),
            (t("commands.language.name"), [{"name": "Common"}, {"name": "abcdef"}]),
            (
                t("commands.search.name"),
                [
                    {"query": "Barb"},
                    {"query": "qwertyuiopasdfghjkl;zxcvbnm,./1234567890"},
                ],
            ),
            (
                t("commands.color.name"),
                [{"hex_color": "#ff00ff"}, {"hex_color": "Not a color"}],
            ),
            (
                t("commands.color.name"),
                {"hex_color": ""},
            ),  # Run clear last, to remove useless data from files.
            (t("commands.stats.name"), {}),
            (
                t("commands.tokengen.name"),
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
                ],
            ),
            (
                t("commands.tokengenurl.name"),
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
                    {"url": "NotAUrl"},
                ],
            ),
            (t("commands.initiative.name"), {}),
            (t("commands.help.name"), {}),
            # ("", {"": "", "": ""}),
        ],
    )
    async def test_slash_commands(
        self,
        commands: list[discord.app_commands.Command],
        cmd_name: str,
        arguments: dict | list[dict],
    ):
        cmd = commands.get(cmd_name)
        assert cmd is not None, f"{cmd_name} command not found"

        if not isinstance(arguments, list):
            arguments = [arguments]  # List required

        for arg_set in arguments:
            arg_variants = self.expand_arg_variants(arg_set)
            for args in arg_variants:
                try:
                    await cmd.callback(itr=self.mock_interaction, **args)
                except Exception as e:
                    pytest.fail(
                        f"Error while running command /{cmd_name} with args {args}: {e}"
                    )
