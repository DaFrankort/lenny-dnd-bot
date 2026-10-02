import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any, cast

import discord
import pytest

from discord.enums import EventStatus

from logic.google_calendar import (
    GoogleCalendarSync,
    build_calendar_event_body,
    build_reminder_message,
    event_calendar_markers,
    is_calendar_opted_in,
    is_reminder_due,
    normalize_calendar_target_name,
)


def create_event(description: str | None = None) -> discord.ScheduledEvent:
    start = datetime(2030, 1, 2, 18, tzinfo=timezone.utc)
    return cast(discord.ScheduledEvent, SimpleNamespace(
        id=123,
        guild=SimpleNamespace(id=456),
        name="Game night",
        description=description,
        start_time=start,
        end_time=None,
        location=None,
        channel=SimpleNamespace(name="Tabletop voice"),
        status=EventStatus.scheduled,
    ))


def test_event_is_opted_in_only_by_marker_line():
    event = create_event("Bring your character sheet.\n#group-1")
    unmarked_event = create_event("We discussed #group-1 before.")

    assert is_calendar_opted_in(event, "group-1")
    assert not is_calendar_opted_in(unmarked_event, "group-1")


def test_event_can_target_multiple_named_calendars():
    event = create_event("#group-1\n#group-2\n#not a valid target")

    assert event_calendar_markers(event) == {"group-1", "group-2"}
    assert normalize_calendar_target_name(" #Group-1 ") == "group-1"


def test_calendar_event_body_strips_markers_and_uses_channel_location():
    event = create_event("Bring your character sheet.\n#group-1\n#group-2")

    body = build_calendar_event_body(event, "group-1")

    assert body["summary"] == "Game night"
    assert body["description"] == "Bring your character sheet.\n\nDiscord event: https://discord.com/events/456/123"
    assert body["location"] == "Tabletop voice"
    assert body["end"]["dateTime"] == (event.start_time + timedelta(hours=1)).isoformat()


def test_reminder_due_for_hour_offset_and_at_start():
    event = create_event()

    assert is_reminder_due(event, event.start_time - timedelta(hours=1), 1)
    assert not is_reminder_due(event, event.start_time - timedelta(hours=1, seconds=1), 1)
    assert not is_reminder_due(event, event.start_time, 0)
    assert is_reminder_due(event, event.start_time, 0, at_start=True)
    assert not is_reminder_due(event, event.start_time + timedelta(minutes=6), 0, at_start=True)

    event.status = EventStatus.canceled
    assert not is_reminder_due(event, event.start_time, 0, at_start=True)


def test_reminder_mentions_configured_role_instead_of_everyone():
    event = create_event()
    role = cast(discord.Role, SimpleNamespace(id=789, mention="<@&789>"))

    message, allowed_mentions = build_reminder_message(event, role, at_start=True)

    assert message.startswith("<@&789>")
    assert "starts now" in message
    assert allowed_mentions.to_dict()["roles"] == [789]


def test_syncs_and_removes_each_marked_calendar_independently(monkeypatch: pytest.MonkeyPatch):
    event = create_event("#group-1\n#group-2")
    config = SimpleNamespace(
        calendar_targets={
            "group-1": SimpleNamespace(calendar_id="calendar-one"),
            "group-2": SimpleNamespace(calendar_id="calendar-two"),
        },
        calendar_event_ids={},
        calendar_sent_reminders=["123:group-1:before", "123:group-2:start"],
    )
    config_handler = SimpleNamespace(config=config, save=lambda: None)
    synced: list[tuple[str, str]] = []
    deleted: list[str] = []

    def upsert(calendar_id: str, google_event_id: str | None, body: dict[str, Any]) -> str:
        synced.append((calendar_id, body["extendedProperties"]["private"]["discordCalendarTarget"]))
        return f"google-{calendar_id}"

    def get_guild_config(guild: discord.Guild) -> SimpleNamespace:
        return config_handler

    def delete(calendar_id: str, event_id: str) -> None:
        deleted.append(calendar_id)

    monkeypatch.setattr("logic.google_calendar._get_guild_config", get_guild_config)
    monkeypatch.setattr("logic.google_calendar._upsert_google_event", upsert)
    monkeypatch.setattr("logic.google_calendar._delete_google_event", delete)

    asyncio.run(GoogleCalendarSync.sync_event(event))

    assert synced == [("calendar-one", "group-1"), ("calendar-two", "group-2")]
    assert config.calendar_event_ids == {123: {"group-1": "google-calendar-one", "group-2": "google-calendar-two"}}
    assert config.calendar_sent_reminders == ["123:group-1:before", "123:group-2:start"]

    event.description = "#group-1"
    asyncio.run(GoogleCalendarSync.sync_event(event))

    assert deleted == ["calendar-two"]
    assert config.calendar_event_ids == {123: {"group-1": "google-calendar-one"}}
    assert config.calendar_sent_reminders == ["123:group-1:before"]

    event.status = EventStatus.canceled
    asyncio.run(GoogleCalendarSync.sync_event(event))

    assert deleted == ["calendar-two", "calendar-one"]
    assert config.calendar_event_ids == {}
    assert config.calendar_sent_reminders == []