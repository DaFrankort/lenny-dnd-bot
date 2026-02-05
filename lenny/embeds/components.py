import abc
import math
from typing import Any, TypeVar

import discord
import discord.ui

from commands.command import get_error_embed
from methods import when

T = TypeVar("T")


class TitleTextDisplay(discord.ui.TextDisplay[discord.ui.LayoutView]):
    """A TextDisplay which is formatted as a title, with optional source and URL."""

    def __init__(self, name: str, source: str | None = None, url: str | None = None):
        title = when(source, f"{name} ({source})", name)
        title = when(url, f"[{title}]({url})", title)
        title = f"### {title}"
        super().__init__(content=title)


class BaseSeparator(discord.ui.Separator[discord.ui.LayoutView]):
    def __init__(self, is_large: bool = False):
        if is_large:
            super().__init__(spacing=discord.SeparatorSpacing.large)
        else:
            super().__init__(spacing=discord.SeparatorSpacing.small)


class BaseLabelTextInput(discord.ui.Label[discord.ui.LayoutView]):
    def __init__(
        self,
        *,
        label: str,
        style: discord.TextStyle = discord.TextStyle.short,
        placeholder: str | None = None,
        required: bool = True,
        min_length: int | None = None,
        max_length: int | None = None,
    ) -> None:
        super().__init__(
            text=label,
            component=discord.ui.TextInput[discord.ui.LayoutView](
                style=style,
                placeholder=placeholder,
                required=required,
                min_length=min_length,
                max_length=max_length,
            ),
        )

    @property
    def input(self) -> discord.ui.TextInput[discord.ui.LayoutView]:
        if isinstance(self.component, discord.ui.TextInput):
            return self.component
        raise TypeError("BaseTextInput component is not a discord.ui.TextInput!")


class ModalSelectComponent(discord.ui.Label[discord.ui.LayoutView]):
    def __init__(
        self,
        *,
        label: str,
        options: list[discord.SelectOption],
        required: bool = True,
        disabled: bool = False,
        placeholder: str | None = None,
    ) -> None:
        super().__init__(
            text=label,
            component=discord.ui.Select(
                options=options,
                required=required,
                disabled=disabled,
                placeholder=placeholder,
            ),
        )

    @property
    def input(self) -> discord.ui.Select[discord.ui.LayoutView]:
        if isinstance(self.component, discord.ui.Select):
            return self.component
        raise TypeError("ModalSelectComponent component is not a discord.ui.Select!")


class BaseModal(discord.ui.Modal):
    def __init__(self, itr: discord.Interaction, title: str):
        super().__init__(title=title)
        self.itr = itr

    async def on_error(self, itr: discord.Interaction, error: Exception):
        embed = get_error_embed(error)
        await itr.response.send_message(embed=embed, ephemeral=True)

    @staticmethod
    def get_str(component: BaseLabelTextInput) -> str | None:
        """Safely parse string from LabeledTextComponent. Returns None if input is empty or only spaces."""
        text = str(component.input).strip()
        return text if text else None

    @staticmethod
    def get_int(component: BaseLabelTextInput) -> int | None:
        """Safely parse integer from LabeledTextComponent. Returns None on failure, defaults to 0 if input is ''"""
        text = str(component.input).strip()
        if text == "":
            return 0
        try:
            return int(text)
        except ValueError:
            return None

    @staticmethod
    def get_choice(component: ModalSelectComponent, result_type: type) -> Any | None:
        """Get the selected choice of a ModalSelectComponent, or None if no choice is selected."""
        if not component.input.values:
            return None
        return result_type(component.input.values[0])

    @staticmethod
    def format_placeholder(text: str, length: int = 100) -> str:
        """Cuts off a string to stay within a modal's 100 character-limit for placeholders."""
        cutoff_str: str = "..."
        length = length - len(cutoff_str)
        return text[:length] + cutoff_str if len(text) > length else text


class PaginatedJumpModal(BaseModal):
    page: BaseLabelTextInput
    view: "PaginatedLayoutView"

    def __init__(self, itr: discord.Interaction, view: "PaginatedLayoutView"):
        super().__init__(itr=itr, title="Jump pages")
        self.view = view
        current_page = str(self.view.page + 1)
        self.page = BaseLabelTextInput(
            label=f"Jump to page (1 - {self.view.max_pages})",
            placeholder=current_page,
            min_length=1,
            max_length=len(str(self.view.max_pages)),
        )
        self.add_item(self.page)


class PaginatedLayoutView(discord.ui.LayoutView):
    """
    Discord LayoutView that supports automatic pagination. To inherit
    from this class, two methods need to be overridden:
    - `build()`, which builds the internal, non-pagination contents.
    - `entry_count`, a property that represents the total number of entries
      in the pagination.

    When overriding `build()`, don't forget to add the pagination footer using
    `self.navigation_footer()` to the container, preferably with a separator.
    """

    page: int
    per_page: int = 10
    modal: PaginatedJumpModal | None

    def __init__(self):
        self.page = 0
        self.modal = None
        super().__init__(timeout=None)

    @abc.abstractmethod
    def build(self) -> None:
        pass

    @property
    @abc.abstractmethod
    def entry_count(self) -> int:
        pass

    @property
    def max_pages(self) -> int:
        return int(math.ceil(self.entry_count / self.per_page))

    def navigation_footer(self) -> discord.ui.ActionRow["PaginatedLayoutView"]:
        disable_back = self.page <= 0
        disable_next = self.page >= self.max_pages - 1
        style = discord.ButtonStyle.primary

        button_first_page = discord.ui.Button["PaginatedLayoutView"](label="↞", style=style)
        button_first_page.callback = self.go_to_first_page
        button_first_page.disabled = disable_back

        button_prev_page = discord.ui.Button["PaginatedLayoutView"](label="←", style=style)
        button_prev_page.callback = self.go_to_prev_page
        button_prev_page.disabled = disable_back

        current_page = f"Page {self.page + 1} / {self.max_pages}"
        button_current_page = discord.ui.Button["PaginatedLayoutView"](label=current_page, style=discord.ButtonStyle.gray)
        button_current_page.callback = self.jump_to_page_sendmodal

        button_next_page = discord.ui.Button["PaginatedLayoutView"](label="→", style=style)
        button_next_page.callback = self.go_to_next_page
        button_next_page.disabled = disable_next

        button_last_page = discord.ui.Button["PaginatedLayoutView"](label="↠", style=style)
        button_last_page.callback = self.go_to_last_page
        button_last_page.disabled = disable_next

        return discord.ui.ActionRow(
            button_first_page,
            button_prev_page,
            button_current_page,
            button_next_page,
            button_last_page,
        )

    async def rebuild(self, itr: discord.Interaction) -> None:
        self.build()
        await itr.response.edit_message(view=self)

    async def go_to_first_page(self, interaction: discord.Interaction):
        self.page = 0
        await self.rebuild(interaction)

    async def go_to_prev_page(self, interaction: discord.Interaction):
        self.page = max(self.page - 1, 0)
        await self.rebuild(interaction)

    async def jump_to_page_sendmodal(self, interaction: discord.Interaction):
        self.modal = PaginatedJumpModal(interaction, self)
        self.modal.on_submit = self.jump_to_page
        await interaction.response.send_modal(self.modal)

    async def jump_to_page(self, interaction: discord.Interaction):
        if not self.modal:
            # This situation should never occur, as this function can only be called
            # after a modal was set in jump_to_page_sendmodal.
            raise RuntimeError("Cannot edit PaginatedJumpModal!")

        page = self.modal.get_int(self.modal.page)

        if page is None:
            raise ValueError("Page must be a positive numerical value!")

        page -= 1  # First page === 0
        page = min(max(page, 0), self.max_pages - 1)
        self.page = page
        return await self.rebuild(interaction)

    async def go_to_next_page(self, interaction: discord.Interaction):
        self.page = min(self.page + 1, self.max_pages - 1)
        return await self.rebuild(interaction)

    async def go_to_last_page(self, interaction: discord.Interaction):
        self.page = self.max_pages - 1
        return await self.rebuild(interaction)
