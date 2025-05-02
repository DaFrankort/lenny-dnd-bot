"""
Parses data from the 5e.tools submodule
"""

import re
from tabulate import tabulate


SPELL_SCHOOLS = {
    "A": "Abjuration",
    "C": "Conjuration",
    "D": "Divination",
    "E": "Enchantment",
    "V": "Evocation",
    "I": "Illusion",
    "N": "Necromancy",
    "P": "Psionic",
    "T": "Transmutation",
}


def format_dnd_text(text: str) -> str:
    text = re.sub(r"\{@action ([^\}]*?)\|([^\}]*?)\}", r"\1", text)
    text = re.sub(r"\{@action ([^\}]*?)\}", r"\1", text)
    text = re.sub(r"\{@adventure ([^\}]*?)\|([^\}]*?)\|([^\}]*?)\}", r"\1 (\2)", text)
    text = re.sub(r"\{@b ([^\}]*?)\}", r"**\1**", text)
    text = re.sub(r"\{@book ([^\}]*?)\|([^\}]*?)\|([^\}]*?)\|([^\}]*?)\}", r"\1", text)
    text = re.sub(r"\{@book ([^\}]*?)\|([^\}]*?)\}", r"\1", text)
    text = re.sub(
        r"\{@chance ([^\}]*?)\|\|\|([^\}]*?)\|([^\}]*?)\}", r"\1 percent", text
    )
    text = re.sub(
        r"\{@classFeature ([^\}]*?)\|([^\}]*?)\|([^\}]*?)\|([^\}]*?)\}", r"\1", text
    )
    text = re.sub(r"\{@condition ([^\}]*?)\|([^\}]*?)\}", r"\1", text)
    text = re.sub(r"\{@condition ([^\}]*?)\}", r"\1", text)
    text = re.sub(r"\{@creature ([^\}]*?)(\|[^\}]*?)?\}", r"__\1__", text)
    text = re.sub(r"\{@d20 -([^\}]*?)\}", r"-\1", text)
    text = re.sub(r"\{@d20 ([^\}]*?)\}", r"+\1", text)
    text = re.sub(r"\{@damage ([^\}]*?)\}", r"**\1**", text)
    text = re.sub(r"\{@dc ([^\}]*?)\}", r"DC \1", text)
    text = re.sub(r"\{@dice ([^\}]*?)\|([^\}]*?)\}", r"\1 (\2)", text)
    text = re.sub(r"\{@dice ([^\}]*?)\}", r"\1", text)
    text = re.sub(r"\{@filter ([^\}]*?)\|([^\}]*?)\|([^\}]*?)\}", r"\1", text)
    text = re.sub(r"\{@filter ([^\}]*?)\|([^\}]*?)\}", r"\1", text)
    text = re.sub(r"\{@filter ([^\}]*?)\}", r"\1", text)
    text = re.sub(r"\{@hazard ([^\}]*?)\|([^\}]*?)\}", r"\1", text)
    text = re.sub(r"\{@hit ([^\}]*?)\}", r"\1", text)
    text = re.sub(r"\{@i ([^\}]*?)\}", r"*\1*", text)
    text = re.sub(r"\{@item ([^\}]*?)\|([^\}]*?)\|([^\}]*?)\}", r"\3", text)
    text = re.sub(r"\{@item ([^\}]*?)\|([^\}]*?)\}", r"\1", text)
    text = re.sub(r"\{@quickref ([^\}]*?)\|([^\}]*?)\|([^\}]*?)\}", r"\1", text)
    text = re.sub(r"\{@race ([^\}]*?)\|\|([^\}]*?)\}", r"\2", text)
    text = re.sub(r"\{@race ([^\}]*?)\|([^\}]*?)\}", r"\1", text)
    text = re.sub(r"\{@race ([^\}]*?)\}", r"\1", text)
    text = re.sub(r"\{@sense ([^\}]*?)\|[^\}]*?\}", r"\1", text)
    text = re.sub(r"\{@sense ([^\}]*?)\}", r"\1", text)
    text = re.sub(r"\{@skill ([^\}]*?)\|([^\}]*?)\}", r"*\1*", text)
    text = re.sub(r"\{@skill ([^\}]*?)\}", r"*\1*", text)
    text = re.sub(r"\{@spell ([^\}]*?)\|([^\}]*?)\}", r"__\1__", text)
    text = re.sub(r"\{@spell ([^\}]*?)\}", r"__\1__", text)
    text = re.sub(r"\{@status ([^\}]*?)\}", r"*\1*", text)
    text = re.sub(r"\{@variantrule ([^\}]*?)\|([^\}]*?)\}", r"\1", text)
    text = re.sub(r"\{@variantrule ([^\}]*?)\}", r"\1", text)

    # Note: notes should be parsed at the end, because they might contain subqueries
    text = re.sub(r"\{@note ([^\}]*?)\}", r"\(\1\)", text)

    return text


def format_spell_level_school(level: int, school: str) -> str:
    if level == 0:
        level_str = "Cantrip"
    else:
        level_str = f"Level {level}"
    return f"{level_str} {SPELL_SCHOOLS[school]}"


def _format_single_casting_time(time: any) -> str:
    amount = time["number"]
    unit = time["unit"]
    note = None

    if "note" in time:
        note = time["note"]

    result = f"Unsupported casting time unit: {unit}"
    if unit == "action":
        if amount == 1:
            result = "Action"
        else:
            result = f"{amount} actions"

    elif unit == "bonus":
        if amount == 1:
            result = "Bonus action"
        else:
            result = f"{amount} bonus actions"

    elif amount == 1:
        result = f"{amount} {unit}"
    else:
        result = f"{amount} {unit}s"

    # Add note, if exists
    if note is not None:
        result = f"{result} ({note})"

    return result


def format_casting_time(time: any) -> str:
    if isinstance(time, list):
        casting_times = [_format_single_casting_time(t) for t in time]
    else:
        casting_times = [_format_single_casting_time(time)]

    return " or ".join(casting_times)


def format_duration_time(duration: any) -> str:
    duration = duration[0]
    if duration["type"] == "instant":
        return "Instantaneous"

    if duration["type"] == "permanent":
        return "Permanent"

    if duration["type"] == "special":
        return "Special"

    if duration["type"] == "timed":
        amount = duration["duration"]["amount"]
        unit = duration["duration"]["type"]
        if amount > 1:
            unit += "s"
        return f"{amount} {unit}"

    return f"Unsupported duration type: '{duration['type']}'"


def format_distance(distance: any) -> str:
    if distance["type"] == "touch":
        return "Touch"

    if distance["type"] == "self":
        return "Self"

    if distance["type"] == "sight":
        return "Sight"

    if distance["type"] == "unlimited":
        return "Unlimited"

    if distance["type"] == "feet":
        if distance["amount"] == 1:
            return "1 foot"
        else:
            return f"{distance['amount']} feet"

    if distance["type"] == "miles":
        if distance["amount"] == 1:
            return "1 mile"
        else:
            return f"{distance['amount']} miles"

    return f"Unsupported distance type: '{distance['type']}'"


def format_range(spell_range: any) -> str:
    if spell_range["type"] == "point":
        return format_distance(spell_range["distance"])

    if spell_range["type"] == "cube":
        return f"Cube ({format_distance(spell_range['distance'])})"

    if spell_range["type"] == "emanation":
        return f"Emanation ({format_distance(spell_range['distance'])})"

    if spell_range["type"] == "radius":
        return f"Radius ({format_distance(spell_range['distance'])})"
    
    if spell_range["type"] == "cone":
        return f"Cone ({format_distance(spell_range['distance'])})"

    return f"Unsupported range type: '{spell_range['type']}'"


def format_components(components: dict) -> str:
    result = []
    if components.get("v", False):
        result.append("V")
    if components.get("s", False):
        result.append("S")
    if "m" in components.keys():
        material = components["m"]
        if not isinstance(material, str):
            material = material["text"]
        result.append(f"M ({material})")
    return ", ".join(result)


def _format_description_block(description: any) -> str:
    if isinstance(description, str):
        return format_dnd_text(description)

    if description["type"] == "quote":
        quote = _format_description_block_from_blocks(description["entries"])
        by = description["by"]
        return f"*{quote}* - {by}"

    if description["type"] == "list":
        bullet = "•"  # U+2022
        points = []
        for item in description["items"]:
            points.append(f"{bullet} {_format_description_block(item)}")
        return "\n".join(points)

    if description["type"] == "inset":
        return f"*{_format_description_block_from_blocks(description['entries'])}*"
    
    if description["type"] == "item":
        name = description["name"]
        entries = [_format_description_block(e) for e in description["entries"]]
        entries = '\n'.join(entries)
        return f"**{name}**: {entries}"
 
    return f"Unsupported description type: '{description['type']}'"


def _format_description_block_from_blocks(descriptions: list[any]) -> str:
    blocks = [_format_description_block(desc) for desc in descriptions]
    return "\n\n".join(blocks)


def _parse_table_value(value: any) -> str:
    if isinstance(value, str):
        return format_dnd_text(value)
    if value["type"] == "cell":
        # Should be improved
        if "roll" in value.keys():
            if "exact" in value["roll"].keys():
                return str(value["roll"]["exact"])
            elif "min" in value["roll"].keys() and "max" in value["roll"].keys():
                roll_min = value["roll"]["min"]
                roll_max = value["roll"]["max"]
                return f"{roll_min}-{roll_max}"

        return f"Unknown table value cell type {value['type']}"

    return f"Unknown table value type {value['type']}"


def _prettify_table(title: str, table: list[list[str]], fallbackUrl: str) -> str:
    widths = [8, 44]
    if len(table[0][0]) > 8:
        widths = [16, 36]

    pretty = tabulate(table, tablefmt="rounded_grid", maxcolwidths=widths)
    if len(pretty) > 1018:
        return f"The table for [{title} can be found here]({fallbackUrl})."
    return f"```{pretty}```"


def _format_description_from_table(
    description: any, fallbackUrl: str
) -> tuple[str, str]:
    caption = description.get("caption", "")
    labels = [format_dnd_text(label) for label in description["colLabels"]]
    rows = [[_parse_table_value(v) for v in row] for row in description["rows"]]

    table = _prettify_table(caption, [labels] + rows, fallbackUrl)
    return (caption, table)


def format_descriptions(
    name: str, description: list[any], fallbackUrl: str
) -> list[tuple[str, str]]:
    subdescriptions: list[tuple[str, str]] = []

    blocks: list[str] = []

    for desc in description:
        # Special case scenario where an entry is a description on its own
        # These will be handled separately
        if isinstance(desc, str):
            blocks.append(format_dnd_text(desc))
        else:
            if desc["type"] == "entries":
                subdescriptions.extend(
                    format_descriptions(desc["name"], desc["entries"], fallbackUrl)
                )
            elif desc["type"] == "table":
                subdescriptions.append(
                    _format_description_from_table(desc, fallbackUrl)
                )
            else:
                blocks.append(_format_description_block(desc))

    descriptions = []
    if len(blocks) > 0:
        descriptions.append((name, blocks[0]))
    for i in range(1, len(blocks)):
        descriptions.append(("", blocks[i]))
    descriptions.extend(subdescriptions)

    return descriptions
