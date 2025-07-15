import os
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
        "cmd_name, args",
        [
            (t("commands.roll.name"), {"diceroll": "1d8+2+1d6", "reason": "Attack"}),
            (t("commands.d20.name"), {}),
            (t("commands.advantage.name"), {"diceroll": "1d20+5", "reason": "Damage"}),
            (t("commands.disadvantage.name"), {"diceroll": "4d8", "reason": "Fire"}),
            (t("commands.shortcut.name"), {}),
            (t("commands.spell.name"), {"name": "Fire Bolt"}),
            (t("commands.item.name"), {"name": "Sword"}),
            (t("commands.condition.name"), {"name": "Poisoned"}),
            (t("commands.creature.name"), {"name": "Goblin"}),
            (t("commands.class.name"), {"name": "Wizard"}),
            (t("commands.rule.name"), {"name": "Action"}),
            (t("commands.action.name"), {"name": "Attack"}),
            (t("commands.feat.name"), {"name": "Tough"}),
            (t("commands.language.name"), {"name": "Common"}),
            (t("commands.search.name"), {"query": "Barb"}),
            # /color is ran twice, to clear the useless data it puts inside of user_colors.json
            (t("commands.color.name"), {"hex_color": "#ff00ff"}),
            (t("commands.color.name"), {"hex_color": None}),
            (t("commands.stats.name"), {}),
            # Generate token commands can't be tested, but generally remain untouched so should rarely break.
            (t("commands.initiative.name"), {}),
            (t("commands.help.name"), {}),
            # ("", {"": "", "": ""}),
        ],
    )
    async def test_commands(self, commands, cmd_name, args):
        cmd = commands.get(cmd_name)
        assert cmd is not None, f"{cmd_name} command not found"

        try:
            await cmd.callback(itr=self.mock_interaction, **args)
        except Exception as e:
            pytest.fail(
                f"Error while running command /{cmd_name} with args {args}: {e}"
            )
