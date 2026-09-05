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
    if not stats.d20_totals:
        return None

    total_rolls = len(stats.d20_totals)
    counts = Counter(stats.d20_totals)

    x_faces = list(range(1, 21))
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

            user_report: list[str] = []
            if not isinstance(assigned_title, str):
                title = assigned_title.name
                user_report.append(f"-# {assigned_title.description}")
            else:
                title = assigned_title
                user_report.append("")

            user_report.append(f"Dice rolled: ``{dice.total_dice_rolled}``")
            user_report.append(f"Average d20 result: ``{dice.average_d20}``")
            user_report.append(f"D20's rolled: ``{len(dice.d20_totals)}``")
            if dice.nat1_count > 0:
                user_report.append(f"Natural 1s rolled: ``{dice.nat1_count}``")
            if dice.nat20_count > 0:
                user_report.append(f"Natural 20s rolled: ``{dice.nat20_count}``")
            if dice.damage_totals:
                user_report.append(f"Total damage: ``{sum(dice.damage_totals)}``")
                user_report.append(f"Average damage: ``{dice.average_dmg}``")
            user_report.append(f"Rolled with Advantage: ``{dice.adv_count}`` time(s)")
            user_report.append(f"Rolled with Disadvantage: ``{dice.dis_count}`` time(s)")

            color = discord.Color(UserColor.get_from_user(user))
            graph = _d20_comparison_chart(dice, color.value)

            users_stats.append(
                UserSessionResult(user=user, color=color, title=title, description="\n- ".join(user_report), graph=graph)
            )

        return SessionResult(base_info="# Session results\nHere's how everyone rolled!", users_stats=users_stats)


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
