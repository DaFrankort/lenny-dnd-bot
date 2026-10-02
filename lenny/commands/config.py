from typing import Protocol, cast

import discord
from discord.app_commands import Range, autocomplete, choices, describe

from commands.command import BaseCommand, BaseCommandGroup
from embeds.config.permissions import ConfigPermissionsView
from embeds.config.sources import ConfigSourcesView
from embeds.embed import ErrorEmbed
from logic.config import OFFICIAL_SOURCES, PARTNERED_SOURCES, Config
from logic.dnd.abstract import fuzzy_matches_list
from logic.dnd.source import ContentChoice
from logic.google_calendar import (
    GoogleCalendarSync,
    normalize_calendar_target_name,
)


class CalendarEventRefresher(Protocol):
    async def refresh_calendar_events(self, guild: discord.Guild) -> None: ...


async def source_autocomplete(itr: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
    sep = "###"  # Required for a fuzzy match of two separate strings that we want to split later.
    current = current.replace(sep, "")
    if not current:
        return []

    entries = []
    try:
        # Value that the user filled in in the `content`-field.
        content_value = itr.data["options"][0]["options"][0]["value"]  # type: ignore
        content = ContentChoice(content_value)

        if content is ContentChoice.OFFICIAL:
            entries = OFFICIAL_SOURCES.entries
        elif content is ContentChoice.PARTNERED:
            entries = PARTNERED_SOURCES.entries
        else:
            entries = OFFICIAL_SOURCES.entries + PARTNERED_SOURCES.entries

    except ValueError:
        return []  # If user fills in `search` before `content`, return nothing.

    matches = fuzzy_matches_list(current, [f"{e.source}{sep}{e.name}" for e in entries])
    results: list[discord.app_commands.Choice[str]] = []
    for result in matches[:25]:
        src, name = result.choice.name.split(sep)
        results.append(discord.app_commands.Choice(name=f"{src} - {name}", value=src))

    return results


class ConfigSourcesCommand(BaseCommand):
    name = "sources"
    desc = "Manage your server's sources!"
    help = "Open up an overview you can use to configure the bot's sources in your server."

    @choices(content=ContentChoice.choices())
    @autocomplete(search=source_autocomplete)
    @describe(
        content="Which 5e.tools tools content to filter for", search="Quickly search for an exact source in the config-list."
    )
    async def handle(self, itr: discord.Interaction, content: str, search: str | None = None):
        config = Config.get(itr)
        content_choice = ContentChoice(content)
        if itr.guild is None:
            embed = ErrorEmbed("Sources can only be managed in a server!")
            await itr.response.send_message(embed=embed, ephemeral=True)
        elif config.user_is_admin_or_has_config_permissions(itr.user):
            view = ConfigSourcesView(itr=itr, allow_configuration=True, content=content_choice, search=search)
            await itr.response.send_message(view=view, ephemeral=True)
        else:
            view = ConfigSourcesView(itr=itr, allow_configuration=False, content=content_choice, search=search)
            await itr.response.send_message(view=view, ephemeral=True)


class ConfigPermissionsCommand(BaseCommand):
    name = "permissions"
    desc = "Manage your server's permissions!"
    help = "Open up an overview you can use to configure the bot's permissions in your server."

    async def handle(self, itr: discord.Interaction):
        config = Config.get(itr)
        if itr.guild is None:
            embed = ErrorEmbed("Permissions can only be managed in a server!")
            await itr.response.send_message(embed=embed, ephemeral=True)
        elif config.user_is_admin(itr.user):
            view = ConfigPermissionsView(itr=itr)
            await itr.response.send_message(view=view, ephemeral=True)
        else:
            embed = ErrorEmbed("You don't have permission to manage permissions!")
            await itr.response.send_message(embed=embed, ephemeral=True)


class ConfigCalendarStatusCommand(BaseCommand):
    name = "status"
    desc = "View Google Calendar sync settings."
    help = "Show the configured shared calendar and reminder settings."

    async def handle(self, itr: discord.Interaction):
        config = Config.get(itr)
        if not config.user_is_admin_or_has_config_permissions(itr.user):
            raise PermissionError("Only admins or users with config permissions can view calendar settings.")

        targets = config.config.calendar_targets
        if not targets:
            await itr.response.send_message("Google Calendar sync is not configured.", ephemeral=True)
            return

        lines: list[str] = []
        for target_name, target in targets.items():
            role = f"<@&{target.reminder_role_id}>" if target.reminder_role_id else "@everyone"
            lead = f"{target.reminder_hours} hour(s) before and at start" if target.reminder_hours else "at start only"
            lines.append(
                f"`#{target_name}`: `{target.calendar_id}`; <#{target.announcement_channel_id}>; "
                f"{role}; reminders {lead}"
            )
        await itr.response.send_message(
            "\n".join(lines),
            ephemeral=True,
        )


class ConfigCalendarAddCommand(BaseCommand):
    name = "add"
    desc = "Add or update a named Google Calendar target."
    help = "Configure a marker, shared calendar, reminder channel, lead time, and optional role."

    @describe(
        target_name="Marker name without # (for example group-1).",
        calendar_id="Google Calendar ID for this group's shared agenda.",
        announcement_channel="Text channel for this group's reminders.",
        reminder_hours="Hours before the event; 0 disables the early reminder but keeps the start reminder.",
        reminder_role="Role to mention instead of @everyone; omit to notify everyone.",
    )
    async def handle(
        self,
        itr: discord.Interaction,
        target_name: str,
        calendar_id: str,
        announcement_channel: discord.TextChannel,
        reminder_hours: Range[int, 0, 168] = 1,
        reminder_role: discord.Role | None = None,
    ):
        if itr.guild is None:
            raise PermissionError("Calendar sync can only be configured in a server.")

        config = Config.get(itr)
        if not config.user_is_admin_or_has_config_permissions(itr.user):
            raise PermissionError("Only admins or users with config permissions can configure calendar sync.")

        target_name = normalize_calendar_target_name(target_name)
        await itr.response.defer(ephemeral=True, thinking=True)
        existing_target = config.config.calendar_targets.get(target_name)
        if existing_target and existing_target.calendar_id != calendar_id:
            await GoogleCalendarSync.clear_target(itr.guild, target_name)
            config = Config.get(itr)

        config.set_calendar_target(
            target_name,
            calendar_id,
            announcement_channel.id,
            reminder_hours,
            reminder_role.id if reminder_role else None,
        )
        client = cast(CalendarEventRefresher, itr.client)
        await client.refresh_calendar_events(itr.guild)

        role_text = reminder_role.mention if reminder_role else "@everyone"
        lead_text = f"{reminder_hours} hour(s) before and at start" if reminder_hours else "at start only"
        await itr.followup.send(
            f"`#{target_name}` now syncs to the configured calendar and mentions {role_text} "
            f"in {announcement_channel.mention} {lead_text}.",
            ephemeral=True,
        )


class ConfigCalendarListCommand(ConfigCalendarStatusCommand):
    name = "list"
    desc = "List configured Google Calendar targets."
    help = "Show all calendar markers, calendars, reminder channels, roles, and reminder times."


class ConfigCalendarRemoveCommand(BaseCommand):
    name = "remove"
    desc = "Remove a named calendar target and its synced events."
    help = "Remove a target's calendar events, reminder settings, and marker mapping."

    async def handle(self, itr: discord.Interaction, target_name: str):
        if itr.guild is None:
            raise PermissionError("Calendar sync can only be configured in a server.")

        config = Config.get(itr)
        if not config.user_is_admin_or_has_config_permissions(itr.user):
            raise PermissionError("Only admins or users with config permissions can configure calendar sync.")

        target_name = normalize_calendar_target_name(target_name)
        await itr.response.defer(ephemeral=True, thinking=True)
        await GoogleCalendarSync.clear_target(itr.guild, target_name)
        await itr.followup.send(f"Calendar target `#{target_name}` was removed.", ephemeral=True)


class ConfigCalendarDisableCommand(BaseCommand):
    name = "disable"
    desc = "Disable Google Calendar sync and reminders."
    help = "Remove the bot's synced calendar events and disable calendar reminders."

    async def handle(self, itr: discord.Interaction):
        config = Config.get(itr)
        if not config.user_is_admin_or_has_config_permissions(itr.user):
            raise PermissionError("Only admins or users with config permissions can disable calendar sync.")
        if itr.guild is None:
            raise PermissionError("Calendar sync can only be configured in a server.")

        await itr.response.defer(ephemeral=True, thinking=True)
        await GoogleCalendarSync.clear_guild(itr.guild)
        await itr.followup.send("Google Calendar sync and reminders are disabled.", ephemeral=True)


class ConfigCalendarCommandGroup(BaseCommandGroup):
    name = "calendar"
    desc = "Configure Google Calendar sync and event reminders."

    def __init__(self):
        super().__init__()
        self.add_command(ConfigCalendarAddCommand())
        self.add_command(ConfigCalendarRemoveCommand())
        self.add_command(ConfigCalendarStatusCommand())
        self.add_command(ConfigCalendarListCommand())
        self.add_command(ConfigCalendarDisableCommand())


class ConfigCommand(BaseCommandGroup):
    name = "config"
    desc = "Configure your server's settings!"

    def __init__(self):
        super().__init__()
        self.add_command(ConfigPermissionsCommand())
        self.add_command(ConfigSourcesCommand())
        self.add_command(ConfigCalendarCommandGroup())
        self.guild_only = True
