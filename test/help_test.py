from bot import Bot
import i18n


class TestHelp:
    def test_all_commands_have_help(self):
        i18n.set_locale("./assets/locales/en.json")
        bot = Bot()
        bot._register_commands()

        command_names = [cmd.name for cmd in bot.tree.get_commands()]

        for name in command_names:
            assert i18n.has(f"commands.{name}.name")
            assert i18n.has(f"commands.{name}.desc")
            assert i18n.has(f"commands.{name}.help")
            assert i18n.has(f"commands.{name}.command")
