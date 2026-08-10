import argparse
import os
from dataclasses import dataclass

from dotenv import load_dotenv


def non_empty_string(value: str) -> str:
    string_value = value.strip()
    if not string_value:
        raise argparse.ArgumentTypeError("Argument cannot be empty or whitespace.")
    return string_value


@dataclass(frozen=True)
class BotConfig:
    token: str
    guild_id: int | None
    voice_enabled: bool
    verbose: bool

    @classmethod
    def load(cls) -> "BotConfig":
        load_dotenv()

        parser = argparse.ArgumentParser(description="Run the Discord bot.")

        parser.add_argument(
            "--verbose",
            action=argparse.BooleanOptionalAction,
            default=False,
            help="Enable additional logging. Disabled by default.",
        )
        parser.add_argument(
            "--voice",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Enable voice behavior. Enabled by default.",
        )
        parser.add_argument(
            "--token",
            type=non_empty_string,
            default=os.getenv("DISCORD_BOT_TOKEN", ""),
            help="Overwrite the discord bot token set in the .env file.",
        )

        guild_id_raw = os.getenv("GUILD_ID")
        default_guild_id = int(guild_id_raw) if guild_id_raw and guild_id_raw.isdigit() else None
        parser.add_argument(
            "--guild",
            type=int,
            default=default_guild_id,
            help="Overwrite the guild id set in the .env file.",
        )

        args = parser.parse_args()

        return cls(
            token=args.token,
            guild_id=args.guild,
            voice_enabled=args.voice,
            verbose=args.verbose,
        )
