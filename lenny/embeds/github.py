import discord

from embeds.components import BaseLabelTextInput, BaseModal
from logic.github import report_issue


class IssueReportModal(BaseModal):
    name = BaseLabelTextInput(
        label="Short Summary of your issue",
        placeholder="A short title, describing your issue.",
    )
    description = BaseLabelTextInput(
        label="Description / Expected Behavior",
        style=discord.TextStyle.paragraph,
    )
    reproduction = BaseLabelTextInput(
        label="Steps to Reproduce?",
        style=discord.TextStyle.paragraph,
        required=False,
    )

    def __init__(self, itr: discord.Interaction):
        super().__init__(itr=itr, title="Report an Issue!")

    async def on_submit(self, itr: discord.Interaction):
        name = self.get_str(self.name)
        description = self.get_str(self.description)
        reproduction = self.get_str(self.reproduction)

        if name is None:
            raise ValueError("Title is required to report an issue!")
        if description is None:
            raise ValueError("You must describe your issue!")

        await report_issue(itr, name, description, reproduction)
