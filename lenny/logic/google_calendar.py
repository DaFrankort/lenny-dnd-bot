import asyncio
import logging
import os
import re
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

import discord
from discord.enums import EventStatus

if TYPE_CHECKING:
    from logic.config import ConfigHandler

CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _get_guild_config(guild: discord.Guild) -> "ConfigHandler":
    from logic.config import Config

    return Config.get_for_guild(guild)


def event_calendar_markers(event: discord.ScheduledEvent) -> set[str]:
    markers: set[str] = set()
    for line in (event.description or "").splitlines():
        marker = line.strip()
        if marker.startswith("#"):
            target_name = marker[1:].casefold()
            if re.fullmatch(r"[a-z0-9][a-z0-9-]{0,31}", target_name):
                markers.add(target_name)
    return markers


def normalize_calendar_target_name(target_name: str) -> str:
    normalized = target_name.strip().removeprefix("#").casefold()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,31}", normalized):
        raise ValueError("Calendar names must use 1-32 lowercase letters, numbers, or hyphens.")
    return normalized


def is_calendar_opted_in(event: discord.ScheduledEvent, target_name: str) -> bool:
    return target_name.casefold() in event_calendar_markers(event)


def build_calendar_event_body(event: discord.ScheduledEvent, target_name: str) -> dict[str, Any]:
    if event.guild is None:
        raise ValueError("Scheduled event is not attached to a guild.")

    start = event.start_time
    end = event.end_time or start + timedelta(hours=1)
    description_lines = [
        line
        for line in (event.description or "").splitlines()
        if not (
            line.strip().startswith("#")
            and re.fullmatch(r"[a-z0-9][a-z0-9-]{0,31}", line.strip()[1:].casefold())
        )
    ]
    description = "\n".join(description_lines).strip()
    discord_url = f"https://discord.com/events/{event.guild.id}/{event.id}"
    if description:
        description = f"{description}\n\nDiscord event: {discord_url}"
    else:
        description = f"Discord event: {discord_url}"

    location = event.location
    if not location and event.channel:
        location = event.channel.name

    body: dict[str, Any] = {
        "summary": event.name,
        "description": description,
        "start": {"dateTime": start.isoformat()},
        "end": {"dateTime": end.isoformat()},
        "extendedProperties": {"private": {"discordEventId": str(event.id), "discordCalendarTarget": target_name}},
    }
    if location:
        body["location"] = location
    return body


def is_reminder_due(event: discord.ScheduledEvent, now: datetime, reminder_hours: int, at_start: bool = False) -> bool:
    if event.status in (EventStatus.canceled, EventStatus.completed):
        return False

    start = event.start_time
    if at_start:
        return start <= now <= start + timedelta(minutes=5)
    if reminder_hours <= 0:
        return False
    return start - timedelta(hours=reminder_hours) <= now < start


def build_reminder_message(
    event: discord.ScheduledEvent,
    role: discord.Role | None,
    at_start: bool,
) -> tuple[str, discord.AllowedMentions]:
    mention = role.mention if role else "@everyone"
    allowed_mentions = discord.AllowedMentions(roles=[role]) if role else discord.AllowedMentions(everyone=True)
    event_name = event.name.replace("@", "@\u200b")
    if at_start:
        timing = "starts now"
    else:
        timing = f"starts <t:{int(event.start_time.timestamp())}:R>"
    return f"{mention} **{event_name}** {timing}.", allowed_mentions


def _get_calendar_service() -> Any:
    from google.oauth2.service_account import Credentials  # pyright: ignore[reportMissingTypeStubs]
    from googleapiclient.discovery import build  # type: ignore

    credentials_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    if not credentials_path:
        raise RuntimeError("Set GOOGLE_SERVICE_ACCOUNT_FILE to the service-account JSON file path.")

    credentials: Any = Credentials.from_service_account_file(  # type: ignore
        credentials_path,
        scopes=CALENDAR_SCOPES,
    )
    service_builder: Any = build  # type: ignore
    return service_builder("calendar", "v3", credentials=credentials, cache_discovery=False)


def _upsert_google_event(calendar_id: str, google_event_id: str | None, body: dict[str, Any]) -> str:
    from googleapiclient.errors import HttpError  # pyright: ignore[reportMissingTypeStubs]

    service = _get_calendar_service()
    if google_event_id:
        try:
            response = service.events().update(calendarId=calendar_id, eventId=google_event_id, body=body).execute()
            return response["id"]
        except HttpError as error:
            response: Any = error.resp
            if getattr(response, "status", None) != 404:
                raise

    response = service.events().insert(calendarId=calendar_id, body=body).execute()
    return response["id"]


def _delete_google_event(calendar_id: str, google_event_id: str) -> None:
    from googleapiclient.errors import HttpError  # pyright: ignore[reportMissingTypeStubs]

    service = _get_calendar_service()
    try:
        service.events().delete(calendarId=calendar_id, eventId=google_event_id).execute()
    except HttpError as error:
        response: Any = error.resp
        if getattr(response, "status", None) != 404:
            raise


class GoogleCalendarSync:
    @staticmethod
    async def sync_event(event: discord.ScheduledEvent) -> None:
        if event.guild is None:
            return

        config_handler = _get_guild_config(event.guild)
        config = config_handler.config
        if not config.calendar_targets:
            return

        original_mappings = config.calendar_event_ids.get(event.id, {})
        event_mappings = dict(original_mappings)
        original_reminders = config.calendar_sent_reminders
        markers: set[str] = event_calendar_markers(event)
        if event.status is EventStatus.canceled:
            markers = set[str]()

        reminder_prefix = f"{event.id}:"
        active_reminders = [
            key
            for key in original_reminders
            if not key.startswith(reminder_prefix) or key.split(":", 2)[1] in markers
        ]
        for target_name, target in list(config.calendar_targets.items()):
            google_event_id = event_mappings.get(target_name)
            if event.status is EventStatus.canceled or target_name not in markers:
                if google_event_id:
                    try:
                        await asyncio.to_thread(_delete_google_event, target.calendar_id, google_event_id)
                    except Exception:
                        logging.exception(
                            "Failed to delete Google Calendar event %s for Discord event %s",
                            target_name,
                            event.id,
                        )
                        continue
                    event_mappings.pop(target_name, None)
                continue

            body = build_calendar_event_body(event, target_name)
            try:
                google_event_id = await asyncio.to_thread(
                    _upsert_google_event,
                    target.calendar_id,
                    google_event_id,
                    body,
                )
            except Exception:
                logging.exception("Failed to sync Discord event %s to calendar %s", event.id, target_name)
                continue

            event_mappings[target_name] = google_event_id

        reminders_changed = active_reminders != original_reminders
        if reminders_changed:
            config.calendar_sent_reminders = active_reminders
        if event_mappings != original_mappings:
            if event_mappings:
                config.calendar_event_ids[event.id] = event_mappings
            else:
                config.calendar_event_ids.pop(event.id, None)
        if reminders_changed or event_mappings != original_mappings:
            config_handler.save()

    @staticmethod
    async def delete_event(event: discord.ScheduledEvent) -> None:
        if event.guild is None:
            return
        await GoogleCalendarSync.delete_event_by_id(event.guild, event.id)

    @staticmethod
    async def delete_event_by_id(guild: discord.Guild, discord_event_id: int) -> None:
        config_handler = _get_guild_config(guild)
        config = config_handler.config
        event_mappings = config.calendar_event_ids.get(discord_event_id, {})
        reminder_prefix = f"{discord_event_id}:"
        if not event_mappings and not any(key.startswith(reminder_prefix) for key in config.calendar_sent_reminders):
            return

        failed_targets: set[str] = set()
        for target_name, google_event_id in event_mappings.items():
            target = config.calendar_targets.get(target_name)
            if not target:
                failed_targets.add(target_name)
                continue
            try:
                await asyncio.to_thread(_delete_google_event, target.calendar_id, google_event_id)
            except Exception:
                logging.exception("Failed to delete Google Calendar event for Discord event %s", discord_event_id)
                failed_targets.add(target_name)

        if failed_targets:
            config.calendar_event_ids[discord_event_id] = {
                name: event_id for name, event_id in event_mappings.items() if name in failed_targets
            }
        else:
            config.calendar_event_ids.pop(discord_event_id, None)
        config.calendar_sent_reminders = [
            key for key in config.calendar_sent_reminders if not key.startswith(reminder_prefix)
        ]
        config_handler.save()

    @staticmethod
    async def clear_target(guild: discord.Guild, target_name: str) -> None:
        config_handler = _get_guild_config(guild)
        config = config_handler.config
        target = config.calendar_targets.get(target_name)
        if not target:
            return

        for event_id, mappings in list(config.calendar_event_ids.items()):
            google_event_id = mappings.get(target_name)
            if not google_event_id:
                continue
            await asyncio.to_thread(_delete_google_event, target.calendar_id, google_event_id)
            mappings.pop(target_name)
            if not mappings:
                config.calendar_event_ids.pop(event_id)

        config.calendar_targets.pop(target_name)
        config.calendar_sent_reminders = [
            key for key in config.calendar_sent_reminders if not key.endswith(f":{target_name}:before")
            and not key.endswith(f":{target_name}:start")
        ]
        config_handler.save()

    @staticmethod
    async def clear_guild(guild: discord.Guild) -> None:
        config_handler = _get_guild_config(guild)
        config = config_handler.config
        for event_mappings in config.calendar_event_ids.values():
            for target_name, google_event_id in event_mappings.items():
                target = config.calendar_targets.get(target_name)
                if target:
                    await asyncio.to_thread(_delete_google_event, target.calendar_id, google_event_id)

        config_handler.clear_calendar_settings()