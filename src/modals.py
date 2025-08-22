import logging
from discord import Interaction
from discord.ui import Label, TextInput, Modal


class SimpleModal(Modal):
    def __init__(self, itr: Interaction, title: str):
        super().__init__(title=title)
        self.itr = itr

    def log_inputs(self, itr: Interaction):
        """Logs all text input values."""
        input_values = {
            child.label: str(child)
            for child in self.children
            if isinstance(child, Label) and str(child) != ""
        }

        username = itr.user.name
        logging.info(f"{username} submitted modal => {input_values}")

    async def on_error(self, itr: Interaction, error: Exception):
        self.log_inputs(itr)
        await itr.response.send_message(
            "Something went wrong! Please try again later.", ephemeral=True
        )
        raise error

    def get_str(self, label_item: Label) -> str | None:
        """Safely parse string from TextInput. Returns None if input is empty or only spaces."""
        component = label_item.component
        if isinstance(component, TextInput):
            text = str(component).strip()
            return text if text else None
        else:
            raise NotImplementedError(
                f"Item type {type(component)} not supported in get_str()"
            )

    def get_int(self, label_item: Label) -> int | None:
        """Safely parse integer from TextInput. Returns None on failure, defaults to 0 if input is ''"""
        component = label_item.component
        if isinstance(component, TextInput):
            text = str(component).strip()
            if text == "":
                return 0
            try:
                return int(text)
            except ValueError:
                return None
        else:
            raise NotImplementedError(
                f"Item type {type(component)} not supported in get_int()"
            )

    def get_choice(
        self, label_item: Label, default: any, choices: dict[str, any]
    ) -> any:
        """Used to simulate selection-menu functionality, allowing a user to select a certain option."""
        logging.warning(
            "Deprecated! Using get_choice is not recommended, consider using an ui.Select component instead."
        )
        # TODO: get_choice may be deprecated in the future, if discord adds select-dropdowns that would be the better option.

        choice = default
        component = label_item.component
        if isinstance(component, TextInput):
            user_input = str(component).lower()
            for key in choices:
                choice_value = choices[key]
                if user_input.startswith(key.lower()):
                    choice = choice_value
                    break

            return choice
        else:
            raise NotImplementedError(
                f"Item type {type(component)} not supported in get_choice()"
            )
