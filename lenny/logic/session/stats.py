from collections import Counter

import discord

from logic.color import UserColor, adjust_rgb_color_lightness, get_luminance
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
    resolved_counts = Counter(stats.resolved_d20_totals)

    x_faces = list(range(1, 21))
    if total_rolls == 0:
        return None

    unresolved_percentages = [((counts[face] - resolved_counts[face]) / total_rolls) * 100 for face in x_faces]
    resolved_percentages = [(resolved_counts[face] / total_rolls) * 100 for face in x_faces]

    fig, ax = empty_distribution_chart(x_faces)
    user_color = to_matplotlib_color(color)  # type: ignore
    user_rgb = UserColor.to_rgb(color)
    luminance = get_luminance(user_rgb)
    resolved_average_lightness = 45.0 if luminance > 0.5 else 90.0
    resolved_average_rgb = adjust_rgb_color_lightness(user_rgb, resolved_average_lightness)
    non_resolved_color = "#{:02X}{:02X}{:02X}".format(*resolved_average_rgb)
    ax.set_xticks(x_faces)  # type: ignore
    ax.axvline(  # type: ignore
        x=stats.average_rolled_d20,
        color="gray",
        linestyle="--",
        label="Average raw",
    )
    ax.axvline(  # type: ignore
        x=stats.average_resolved_d20,
        color="white",
        linestyle="--",
        alpha=0.5,
        label="Average resolved",
    )

    ax.bar(  # type: ignore
        x_faces,
        unresolved_percentages,
        bottom=resolved_percentages,
        color=non_resolved_color,
        alpha=0.7,
        label="Unresolved d20s",
    )
    ax.bar(x_faces, resolved_percentages, color=user_color, label="Resolved d20s")  # type: ignore
    style_legend(ax.legend(loc="best"))  # type: ignore

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
