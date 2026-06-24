import discord
import urllib.parse

from embeds.embed import BaseEmbed


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
    discord_context = _format_to_collapsable_section(label="Discord Metadata", content=_get_itr_report(itr))

    body = [discord_context, f"\n## Description\n{description.strip()}"]
    if reproduction:
        body.append(f"## How to Reproduce\n{reproduction.strip()}")

    base_url = "https://github.com/DaFrankort/lenny-dnd-bot/issues/new"
    body_str = "\n".join(body)
    params = {"title": title.strip(), "body": body_str}

    final_url = f"{base_url}?{urllib.parse.urlencode(params)}"
    embed = BaseEmbed(title="Finish your report on GitHub!", description=final_url)
    embed.url = final_url
    await itr.response.send_message(embed=embed, ephemeral=False)
