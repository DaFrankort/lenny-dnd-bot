import discord

from commands.command import BaseCommand
from embeds.github import IssueReportModal


class IssueReportCommand(BaseCommand):
    name = "issue"
    desc = "Report an issue, or request a feature for the bot!"
    help = "Reports a bug or requests a feature directly to the developers."

    async def handle(self, itr: discord.Interaction):
        await itr.response.send_modal(IssueReportModal(itr))
