import os
import urllib.parse

import discord
from github import Auth, GithubIntegration

from embeds.embed import BaseEmbed

GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
GITHUB_INSTALLATION_ID = os.getenv("GITHUB_INSTALLATION_ID")
GITHUB_PRIVATE_KEY = os.getenv("GITHUB_PRIVATE_KEY")
GITHUB_REPO_PATH = os.getenv("GITHUB_REPO_PATH")


def _get_itr_report(itr: discord.Interaction) -> str:
    user = itr.user
    guild = itr.guild
    channel = itr.channel

    body: list[str] = []

    body.extend(["### User", f"- Name: `{user}`", f"- ID: `{user.id}`"])
    if guild and isinstance(user, discord.Member):
        body.append(f"- Nickname: ``{user.nick}``")

    if user.is_on_mobile:  # type: ignore
        body.append("- User was potentially using mobile.")

    if guild:
        body.extend(["### Guild", f"- Name: `{guild.name}`", f"- ID: `{guild.id}`", f"- Member Count: `{guild.member_count}`"])
    else:
        body.append("- No guild data available.")

    if channel is not None:
        body.append("### Channel")
        if channel.name:  # type: ignore
            body.append(f"- Name: `#{channel.name}`")  # type: ignore
        body.append(f"- ID: `{channel.id}`")
        body.append(f"- Type: `{channel.type.name}`")

    return "\n".join(body)


def _format_to_collapsable_section(label: str, content: str) -> str:
    return f"<details>\n<summary>{label}</summary>\n\n{content}\n</details>\n"


async def report_issue(itr: discord.Interaction, title: str, description: str, reproduction: str | None):
    await itr.response.defer()
    discord_context = _format_to_collapsable_section(label="Discord Metadata", content=_get_itr_report(itr))

    body = [discord_context, f"\n## Description\n{description.strip()}"]
    if reproduction:
        body.append(f"## How to Reproduce\n{reproduction.strip()}")

    base_url = f"https://github.com/{GITHUB_REPO_PATH}/issues/new"
    body_str = "\n".join(body)

    try:
        if GITHUB_APP_ID is None or GITHUB_INSTALLATION_ID is None or GITHUB_REPO_PATH is None or GITHUB_PRIVATE_KEY is None:
            raise SystemError("GitHub App is not configured correctly.")

        with open(GITHUB_PRIVATE_KEY, "r") as f:
            private_key_content = f.read()

        auth = Auth.AppAuth(GITHUB_APP_ID, private_key_content)
        gi = GithubIntegration(auth=auth)

        g = gi.get_github_for_installation(int(GITHUB_INSTALLATION_ID))
        repo = g.get_repo(GITHUB_REPO_PATH)

        loop = itr.client.loop
        issue = await loop.run_in_executor(
            None, lambda: repo.create_issue(title=title.strip(), body=body_str, labels=["discord"])
        )

        embed = BaseEmbed(
            title=f"Created Issue #{issue.number} - {title}",
            description="Your report has been logged directly to GitHub.",
        )
        embed.url = issue.html_url
        await itr.followup.send(embed=embed)

    except Exception as e:
        params = {"title": title.strip(), "body": body_str}
        final_url = f"{base_url}?{urllib.parse.urlencode(params)}"
        embed = BaseEmbed(
            title="Finish your report on GitHub!",
            description=f"``{e}``\n\nDue to an error, we could not automatically publish your ticket.\nPlease click the title to finish your report using GitHub!\n",
            color=discord.Color.orange(),
        )
        embed.url = final_url
        await itr.followup.send(embed=embed, ephemeral=True)
