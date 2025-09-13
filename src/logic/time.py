from datetime import datetime

from embed import SimpleEmbed


TIME_MULTIPLIERS = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
    "w": 604800,
}


class RelativeTimestampEmbed(SimpleEmbed):
    def __init__(self, timestamp: str):
        super().__init__(title=timestamp, description=f"```{timestamp}```")


def get_relative_timestamp(start: datetime, delay_seconds: int | float) -> str:
    time = start.replace(second=0, microsecond=0)
    base_time = int(time.timestamp())
    unix_timestamp = base_time + int(delay_seconds)
    return f"<t:{unix_timestamp}:R>"
