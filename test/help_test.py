from bot import Bot
from help import (
    _format_command_list_item,
    _get_default_help_inline_fields,
)


class TestHelp:
    def test_all_commands_mentioned(self):
        """
        Tests that the default /help command mentions every single command.
        """
        bot = Bot()
        bot._register_commands()

        command_names = [
            _format_command_list_item(cmd.name) for cmd in bot.tree.get_commands()
        ]
        inline_fields = _get_default_help_inline_fields()
        mentioned_commands = [
            _format_command_list_item("help")
        ]  # Help is not mentioned in inline fields by design.

        for field in inline_fields:
            for line in field._descriptions:
                mentioned_commands.append(line)

        for cmd_name in command_names:
            assert (
                cmd_name in mentioned_commands
            ), f"Command '/{cmd_name}' not mentioned in general /help tab."
