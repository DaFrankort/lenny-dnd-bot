from collections import Counter

import discord

from logic.color import UserColor
from logic.graphs import (
    convert_and_close_fig,
    empty_distribution_chart,
    style_legend,
    to_matplotlib_color,
)
from logic.roll import MultiRollResult, RollResult
from logic.session.titles import TitleRegistry
from logic.session.types import (
    SessionResult,
    UserSessionDiceStats,
    UserSessionResult,
    UserSessionStats,
)


def _d20_comparison_chart(stats: UserSessionDiceStats, color: int) -> discord.File | None:
    if not stats.rolled_d20_totals:
        return None

    total_rolls = len(stats.rolled_d20_totals)
    counts = Counter(stats.rolled_d20_totals)

    x_faces = list(range(1, 21))
    if total_rolls == 0:
        return None

    actual_percentages = [(counts[face] / total_rolls) * 100 for face in x_faces]
    average_percentage = 5.0

    fig, ax = empty_distribution_chart(x_faces)
    ax.set_xticks(x_faces)  # type: ignore
    ax.axhline(y=average_percentage, color="white", linestyle="--", alpha=0.5, label=f"Average ({average_percentage}%)")  # type: ignore

    user_color = to_matplotlib_color(color)  # type: ignore
    ax.bar(x_faces, actual_percentages, color=user_color, label="Your d20 Rolls")  # type: ignore

    style_legend(ax.legend(loc="upper right"))  # type: ignore

    buf = convert_and_close_fig(fig)

    return discord.File(fp=buf, filename=f"{color}_d20_comparison.png")


class SessionStats:
    user_data: dict[int, UserSessionStats]
    _start: float

    def __init__(self, itr: discord.Interaction):
        self._start = itr.created_at.timestamp()
        self.user_data = {}

    @property
    def timestamp(self) -> str:
        return f"<t:{self._start}:R>"

    def add_roll(self, itr: discord.Interaction, result: RollResult | MultiRollResult):
        if itr.user.bot:
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

            if not isinstance(assigned_title, str):
                title = assigned_title.name
                title_description = f"-# {assigned_title.description}"
            else:
                title = assigned_title
                title_description = ""

            color = discord.Color(UserColor.get_from_user(user))
            graph = _d20_comparison_chart(dice, color.value)

            users_stats.append(
                UserSessionResult(
                    user=user,
                    color=color,
                    title=title,
                    title_description=title_description,
                    dice=dice,
                    graph=graph,
                )
            )

        base_info = ["# Session stats"]
        if len(users_stats) > 0:
            base_info.append("Here's everyone's results:")
        else:
            base_info.append("No users have rolled yet!")

        return SessionResult(base_info="\n".join(base_info), users_stats=users_stats)


class GlobalSessionStats:
    _sessions: dict[int, SessionStats]

    def __init__(self):
        self._sessions = {}

    def _get_itr_id(self, itr: discord.Interaction) -> int:
        if not itr.channel:
            raise PermissionError("Can only track sessions from a text channel in a server.")
        return itr.channel.id

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
            raise ValueError("Session is already active for this voice-chat!")

        self._sessions[session_id] = SessionStats(itr)
        return self._sessions[session_id]

    def stop(self, itr: discord.Interaction) -> SessionStats:
        session_id = self._get_itr_id(itr)
        if session_id not in self._sessions:
            raise KeyError("Session can't be stopped since it does not exist.")

        stats = self._sessions[session_id]
        del self._sessions[session_id]
        return stats

    def add_roll(self, itr: discord.Interaction, result: RollResult | MultiRollResult) -> SessionStats | None:
        stats = self.get(itr)
        if stats:
            stats.add_roll(itr, result)
        return stats


SessionStatistics = GlobalSessionStats()
