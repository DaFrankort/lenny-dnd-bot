from discord.app_commands import Choice
from rapidfuzz import fuzz


def get_autocomplete_suggestions_from_list(
    strings: list[str],
    query: str = "",
    show_results_on_empty_query: bool = False,
    fuzzy_threshold: float = 75,
    limit: int = 25,
) -> list[Choice[str]]:
    query = query.strip().lower().replace(" ", "")

    if query == "":
        if show_results_on_empty_query:
            return [
                Choice(name=string.strip().title(), value=string)
                for string in strings[:limit]
            ]
        else:
            return []

    choices = []
    seen = set()  # Required to avoid duplicate suggestions
    for string in strings:
        if string.strip() in seen:
            continue

        string_clean = string.strip().lower().replace(" ", "")
        score = fuzz.partial_ratio(query, string_clean)
        if score > fuzzy_threshold:
            starts_with_query = string_clean.startswith(query)
            choices.append(
                (starts_with_query, score, Choice(name=string.strip(), value=string))
            )
            seen.add(string.strip())

    choices.sort(
        key=lambda x: (-x[0], -x[1], x[2].name)
    )  # Sort by query match => fuzzy score => alphabetically
    return [choice for _, _, choice in choices[:limit]]
