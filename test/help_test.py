from bot import Bot
from help import HelpTabs, _format_description_point, _get_default_help_inline_fields, _get_help_fields


class TestHelp:
    def test_tab_has_fields(self):
        """
        Test that the `_get_help_fields` function returns the correct title and fields for each HelpTab.
        Helps to ensure that each HelpTab has actual documentation in /help.
        """
        default_title, default_fields = _get_help_fields(HelpTabs.Default)

        for tab in HelpTabs:
            if tab == HelpTabs.Default:
                continue

            title, fields = _get_help_fields(tab)

            assert (
                title != default_title
            ), f"Title for HelpTab `{tab.name}` should not resolve to default title."
            assert (
                fields != default_fields
            ), f"Fields for HelpTab `{tab.name}` should not resolve to default fields."

    def test_all_commands_mentioned(self):
        """
        Tests that the default /help command mentions every single command.
        """
        bot = Bot()
        bot._register_commands()

        command_names = [_format_description_point(cmd.name) for cmd in bot.tree.get_commands()]
        inline_fields = _get_default_help_inline_fields()
        mentioned_commands = [
            _format_description_point("help")
        ]  # Help is not mentioned in inline fields by design.

        for field in inline_fields:
            for line in field._descriptions:
                mentioned_commands.append(line)

        for cmd_name in command_names:
            assert (
                cmd_name in mentioned_commands
            ), f"Command '/{cmd_name}' not mentioned in general /help tab."
