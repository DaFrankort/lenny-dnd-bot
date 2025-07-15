import discord
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

from bot import Bot
import i18n
from i18n import t

i18n.set_locale("./assets/locales/en.json")


class TestBotCommands:
    @pytest.fixture()
    def bot(self):
        bot = Bot(voice=False)
        bot._register_commands()
        return bot

    @pytest.fixture()
    def commands(self, bot):
        print([c.name for c in bot.tree.get_commands()])
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

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "cmd_name, arguments",
        [
            (
                t("commands.roll.name"),
                [
                    {"diceroll": "1d8+2+1d6", "reason": None},
                    {"diceroll": "1d20+5", "reason": "Attack"},
                    {"diceroll": "Bad Roll", "reason": "1d20"},
                ],
            ),
            (t("commands.d20.name"), {}),
            (
                t("commands.advantage.name"),
                [
                    {"diceroll": "1d8+2+1d6", "reason": None},
                    {"diceroll": "1d20+5", "reason": "Attack"},
                    {"diceroll": "Bad Roll", "reason": "1d20"},
                ],
            ),
            (
                t("commands.disadvantage.name"),
                [
                    {"diceroll": "1d8+2+1d6", "reason": None},
                    {"diceroll": "1d20+5", "reason": "Attack"},
                    {"diceroll": "Bad Roll", "reason": "1d20"},
                ],
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
            # Generate token commands can't be tested, but generally remain untouched so should rarely break.
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

        if isinstance(arguments, dict):
            arguments = [arguments]  # List required

        for args in arguments:
            try:
                await cmd.callback(itr=self.mock_interaction, **args)
            except Exception as e:
                pytest.fail(
                    f"Error while running command /{cmd_name} with args {args}: {e}"
                )
