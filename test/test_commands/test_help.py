from bot import Bot
from commands.command import BaseCommand


class TestHelp:
    def test_all_commands_have_help(self):
        bot = Bot()

        commands = [cmd for cmd in bot.tree.get_commands() if isinstance(cmd, BaseCommand)]

        for cmd in commands:
            # Assert that every command has a name, desc, help, and command
            assert cmd.name is not None, f"No 'name' available for {cmd}"
            assert cmd.desc is not None, f"No 'desc' available for {cmd.name}"
            assert cmd.help is not None, f"No 'help' available for {cmd.name}"
            assert cmd.command is not None, f"No 'command' available for {cmd.name}"
