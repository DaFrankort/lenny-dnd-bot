import datetime

import discord


def get_week_phrase(in_weeks: int) -> str:
    if in_weeks == 0:
        return "this week"
    elif in_weeks == 1:
        return "next week"
    return f"in {in_weeks} weeks"


def get_week_choice_name(in_weeks: int, today: datetime.date | None = None) -> str:
    phrase = get_week_phrase(in_weeks).capitalize()
    if in_weeks == 0:
        return phrase

    today = today or datetime.date.today()
    week_start = today + datetime.timedelta(days=in_weeks * 7 - today.weekday())
    date_range = f"{week_start:%d %b}"
    return f"{phrase} ({date_range})"


async def in_weeks_autocomplete(_: discord.Interaction, current: str) -> list[discord.app_commands.Choice[int]]:
    query = current.strip().casefold()
    choices: list[discord.app_commands.Choice[int]] = []

    for in_weeks in range(49):
        name = get_week_choice_name(in_weeks)
        if query and query not in name.casefold() and not str(in_weeks).startswith(query):
            continue

        choices.append(discord.app_commands.Choice(name=name, value=in_weeks))
        if len(choices) == 25:
            break

    return choices
