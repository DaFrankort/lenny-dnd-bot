import discord

from logic.color import UserColor
from logic.roll import RollResult
from logic.session.titles import TitleRegistry
from logic.session.types import (
    SessionResult,
    UserSessionDiceStats,
    UserSessionResult,
    UserSessionStats,
)


class SessionStats:
    user_data: dict[int, UserSessionStats]
    _start: float

    def __init__(self, itr: discord.Interaction):
        if not isinstance(itr.user, discord.Member):
            raise PermissionError("Interaction must belong to a user.")
        if not itr.user.voice:
            raise PermissionError("Session stats can only be tracked for users in a voice-chat.")
        if not itr.user.voice.channel:
            raise PermissionError("User not in a valid voice channel.")

        self._start = itr.created_at.timestamp()
        self.user_data = {}
        for member in itr.user.voice.channel.members:
            if member.bot:
                continue
            self.user_data[member.id] = UserSessionStats()

    @property
    def timestamp(self) -> str:
        return f"<t:{self._start}:R>"

    def _check_user(self, itr: discord.Interaction) -> bool:
        if not isinstance(itr.user, discord.Member):
            return False
        if not itr.user.voice:
            return False
        if itr.user.bot:
            return False
        return True

    def add_roll(self, itr: discord.Interaction, result: RollResult):
        if not self._check_user(itr):
            return
        if itr.user.id not in self.user_data:
            self.user_data[itr.user.id] = UserSessionStats()
        self.user_data[itr.user.id].dice.add(result)

    def get_report(self, itr: discord.Interaction) -> SessionResult:
        if not itr.guild:
            raise PermissionError("Must be in a server to get a report!")

        title_registry = TitleRegistry()
        users_stats: list[UserSessionResult] = []
        for user_id, stats in self.user_data.items():
            user = itr.guild.get_member(user_id)
            if not user:
                continue

            dice: UserSessionDiceStats = stats.dice

            assigned_title = title_registry.assign_title(dice, self.user_data) or "Adventurer"

            user_report: list[str] = []
            if not isinstance(assigned_title, str):
                title = assigned_title.name
                user_report.append(f"-# {assigned_title.description}")
            else:
                title = assigned_title

            user_report.append(f"Average d20 result: ``{dice.average_d20}``")
            user_report.append(f"Average damage: ``{dice.average_dmg}``")
            user_report.append(f"Dice rolled: ``{dice.dice_rolled}``")

            users_stats.append(
                UserSessionResult(
                    user=user,
                    color=discord.Color(UserColor.get_from_user(user)),
                    title=title,
                    description="\n- ".join(user_report),
                )
            )

        return SessionResult(base_info="# Session results\nHere's how everyone rolled!", users_stats=users_stats)


class GlobalSessionStats:
    _sessions: dict[int, SessionStats]

    def __init__(self):
        self._sessions = {}

    def _get_itr_id(self, itr: discord.Interaction) -> int:
        if not isinstance(itr.user, discord.Member):
            raise PermissionError("Interaction must belong to a user.")
        if not itr.user.voice:
            raise PermissionError("Session stats can only be tracked for users in a voice-chat.")
        if not itr.user.voice.channel:
            raise PermissionError("User not in a valid voice channel.")

        return itr.user.voice.channel.id

    def get(self, itr: discord.Interaction) -> SessionStats | None:
        try:
            session_id = self._get_itr_id(itr)
        except PermissionError:
            return None

        if session_id not in self._sessions:
            return None
        return self._sessions[session_id]

    def start(self, itr: discord.Interaction) -> SessionStats:
        session_id = self._get_itr_id(itr)
        if session_id in self._sessions:
            raise KeyError("Session is already active for this voice-chat!")
        self._sessions[session_id] = SessionStats(itr)
        return self._sessions[session_id]

    def stop(self, voice_id: int):
        if voice_id not in self._sessions:
            raise KeyError("Session can't be stopped since it does not exist.")
        del self._sessions[voice_id]


SessionStatistics = GlobalSessionStats()
