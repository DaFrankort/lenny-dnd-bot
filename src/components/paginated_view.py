import abc
import math
import discord

from modals import SimpleModal


class PaginatedJumpModal(SimpleModal):
    page: discord.ui.TextInput["PaginatedLayoutView"]
    view: "PaginatedLayoutView"

    def __init__(self, itr: discord.Interaction, view: "PaginatedLayoutView"):
        super().__init__(itr=itr, title="Jump pages")
        self.view = view
        current_page = str(self.view.page + 1)
        self.page = discord.ui.TextInput(
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

    def __init__(self):
        self.page = 0
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
        button_first_page.callback = lambda interaction: self.go_to_first_page(interaction)
        button_first_page.disabled = disable_back

        button_prev_page = discord.ui.Button["PaginatedLayoutView"](label="←", style=style)
        button_prev_page.callback = lambda interaction: self.go_to_prev_page(interaction)
        button_prev_page.disabled = disable_back

        current_page = f"Page {self.page + 1} / {self.max_pages}"
        button_current_page = discord.ui.Button["PaginatedLayoutView"](label=current_page, style=discord.ButtonStyle.gray)
        button_current_page.callback = lambda interaction: self.jump_to_page_sendmodal(interaction)

        button_next_page = discord.ui.Button["PaginatedLayoutView"](label="→", style=style)
        button_next_page.callback = lambda interaction: self.go_to_next_page(interaction)
        button_next_page.disabled = disable_next

        button_last_page = discord.ui.Button["PaginatedLayoutView"](label="↠", style=style)
        button_last_page.callback = lambda interaction: self.go_to_last_page(interaction)
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

    async def go_to_first_page(self, itr: discord.Interaction):
        self.page = 0
        await self.rebuild(itr)

    async def go_to_prev_page(self, itr: discord.Interaction):
        self.page = max(self.page - 1, 0)
        await self.rebuild(itr)

    async def jump_to_page_sendmodal(self, itr: discord.Interaction):
        self.modal = PaginatedJumpModal(itr, self)
        self.modal.on_submit = lambda i: self.jump_to_page(i)
        await itr.response.send_modal(self.modal)

    async def jump_to_page(self, itr: discord.Interaction):
        page = self.modal.get_int(self.modal.page)

        if page is None:
            error_message = "❌ Page must be a positive numerical value! ❌"
            await itr.response.send_message(error_message, ephemeral=True)
            return

        page -= 1  # First page === 0
        page = min(max(page, 0), self.max_pages - 1)
        self.page = page
        return await self.rebuild(itr)

    async def go_to_next_page(self, itr: discord.Interaction):
        self.page = min(self.page + 1, self.max_pages - 1)
        return await self.rebuild(itr)

    async def go_to_last_page(self, itr: discord.Interaction):
        self.page = self.max_pages - 1
        return await self.rebuild(itr)
