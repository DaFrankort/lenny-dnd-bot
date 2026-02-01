import logging

from discord import AppCommandType, Interaction


def log_application_command_interaction(itr: Interaction):
    if not itr.command:
        return
    command_type = getattr(itr.command, "type", None)

    # Context menu interaction
    if command_type in (AppCommandType.user, AppCommandType.message):
        logging.info("%s => %s", itr.user.name, itr.command.name)
        return

    # Slash command
    try:
        criteria = [f"[{k}={v}]" for k, v in vars(itr.namespace).items()]
    except Exception as e:  # pylint: disable=broad-except
        logging.error(e)
        criteria = []

    criteria_text = " ".join(criteria)
    cmd_name = itr.command.qualified_name if itr.command else "???"

    logging.info("%s => /%s %s", itr.user.name, cmd_name, criteria_text)


def log_component_interaction(itr: Interaction):
    component_type = itr.data.get("component_type") if itr.data else None
    if component_type == 3:  # DROPDOWN
        values = ",".join(itr.data["values"]) if itr.data and "values" in itr.data else ""
        values = f"[{values}]"

        logging.info("%s selected %s", itr.user.name, values)

    elif component_type == 2:  # BUTTON
        btn_id = itr.data.get("custom_id") if itr.data else None
        if not btn_id:
            return

        logging.info("%s pressed %s", itr.user.name, btn_id)


def log_modal_submit_interaction(itr: Interaction):
    fields: list[str] = []
    if not itr.data or "components" not in itr.data:
        return

    for component in itr.data["components"]:
        c = component.get("component", {})
        if c.get("value", None) and isinstance(c.get("value"), str):
            fields.append(c.get("value", ""))
        elif c.get("values", None) and isinstance(c.get("values"), list):
            values = ", ".join(c.get("values", []))
            fields.append(f"[{values}]")

    logging.info("%s submitted modal => %s", itr.user.name, "; ".join(fields))
