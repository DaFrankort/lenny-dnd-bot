import datetime
import re
import discord


TIME_MULTIPLIERS = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
    "w": 604800,
}


def _get_relative_timestamp(start: datetime, delay_seconds: int | float) -> str:
    time = start.replace(second=0, microsecond=0)
    base_time = int(time.timestamp())
    unix_timestamp = base_time + int(delay_seconds)
    return f"<t:{unix_timestamp}:R>"


def get_relative_timestamp_from_now(
    seconds: int, minutes: int, hours: int, days: int, weeks: int
) -> str:
    now = discord.utils.utcnow()
    total_seconds = (
        seconds * TIME_MULTIPLIERS["s"]
        + minutes * TIME_MULTIPLIERS["m"]
        + hours * TIME_MULTIPLIERS["h"]
        + days * TIME_MULTIPLIERS["d"]
        + weeks * TIME_MULTIPLIERS["w"]
    )

    timestamp = _get_relative_timestamp(start=now, delay_seconds=total_seconds)
    return timestamp


def get_relative_timestamp_from_message(message: discord.Message) -> tuple[bool, str]:
    regex = r"(\d+(?:[.,]\d+)?)\s*([smhdw])"
    matches = re.findall(regex, message.content, re.IGNORECASE)
    if not matches:
        return False, "Couldn't find any mention of times in that message."

    seconds = 0
    for amount, unit in matches:
        unit = unit.lower()
        if unit not in TIME_MULTIPLIERS:
            continue
        amount = amount.replace(",", ".")
        seconds += float(amount) * TIME_MULTIPLIERS[unit]

    timestamp = _get_relative_timestamp(message.created_at, seconds)
    return True, timestamp


def _parse_date_from_string(date: str) -> datetime.date:
    parts = date.split("/")

    if len(parts) == 1:  # DD
        day = int(parts[0])
        month = discord.utils.utcnow().month
        year = discord.utils.utcnow().year
        date = f"{day:02d}/{month:02d}/{year}"

    elif len(parts) == 2:  # DD/MM
        day, month = map(int, parts)
        year = discord.utils.utcnow().year
        date = f"{day:02d}/{month:02d}/{year}"

    elif len(parts) == 3:  # DD/MM/YYYY
        pass
    else:
        raise ValueError("Invalid date format")

    base_date = datetime.datetime.strptime(date, "%d/%m/%Y").date()
    return base_date


def get_date_timestamp(time: str, timezone: int, date: str) -> tuple[bool, int | str]:
    base_date = discord.utils.utcnow().date()
    if date:
        date = date.replace(".", "/").strip()
        try:
            base_date = _parse_date_from_string(date)
        except Exception:
            return (
                False,
                "Date must be in `DD`, `DD/MM`, or `DD/MM/YYYY` format, and must be a valid date!",
            )

    time = time.replace(":", "").strip()
    if not time.isdigit() or not (1 <= len(time) <= 4):
        return (
            False,
            "Time must be in HHMM or HH format (e.g. `0930`, `15:45`, `700`, or `7`).",
        )

    if len(time) <= 2:
        time = f"{time}00"
    time = time.zfill(4)

    hours, minutes = divmod(int(time), 100)
    try:
        dt = datetime.datetime.combine(
            base_date, datetime.time(hour=hours, minute=minutes)
        )
    except ValueError as e:
        return False, f"Invalid time: {e}"

    dt_utc = dt - datetime.timedelta(hours=timezone)  # Adjust for timezone
    unix_timestamp = int(dt_utc.replace(tzinfo=datetime.timezone.utc).timestamp())
    return True, unix_timestamp
