import discord
from bot import Bot
import i18n


class TestHelp:
    def test_all_commands_have_help(self):
        i18n.set_locale("./assets/locales/en.json")
        bot = Bot()
        bot._register_commands()

        command_names = [
            cmd.name
            for cmd in bot.tree.get_commands()
            if isinstance(cmd, discord.app_commands.Command)
        ]

        for name in command_names:
            assert i18n.has(
                f"commands.{name}.name"
            ), f"No localisation 'name' available for {name}"
            assert i18n.has(
                f"commands.{name}.desc"
            ), f"No localisation 'desc' available for {name}"
            assert i18n.has(
                f"commands.{name}.help"
            ), f"No localisation 'help' available for {name}"
            assert i18n.has(
                f"commands.{name}.command"
            ), f"No localisation 'command' available for {name}"
