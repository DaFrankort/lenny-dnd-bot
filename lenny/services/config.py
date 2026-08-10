import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class BotConfig:
    token: str
    guild_id: int | None
    voice_enabled: bool

    @classmethod
    def load_from_env(cls, voice_enabled: bool = True) -> "BotConfig":
        load_dotenv()

        token = os.getenv("DISCORD_BOT_TOKEN", "")
        guild_id_raw = os.getenv("GUILD_ID")
        guild_id = int(guild_id_raw) if guild_id_raw else None

        return cls(token=token, guild_id=guild_id, voice_enabled=voice_enabled)
