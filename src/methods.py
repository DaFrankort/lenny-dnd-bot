import discord


def when(condition: bool, value_on_true: any, value_on_false: any) -> any:
    """Wrapper method for a ternary statement, for readability"""
    return value_on_true if condition else value_on_false


def simple_choice(choice: str) -> discord.app_commands.Choice:
    return (discord.app_commands.Choice(name=choice, value=choice),)
