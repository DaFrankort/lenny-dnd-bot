import abc
import math

import discord

from components.items import BaseLabelTextInput
from components.modals import BaseModal


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
