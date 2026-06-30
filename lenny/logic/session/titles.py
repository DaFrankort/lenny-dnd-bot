from abc import ABC, abstractmethod

from logic.session.types import UserSessionDiceStats, UserSessionStats


class SessionTitle(ABC):
    name: str
    description: str

    @abstractmethod
    def evaluate(self, stats: UserSessionDiceStats, all_session_stats: dict[int, UserSessionStats]) -> float:
        """
        Returns a score representing how well the player qualifies for this title.
        Return 0 or negative if they don't qualify at all.
        """
        raise NotImplementedError(f"The title '{self.name}' can not be evaluated yet.")


class TitleRegistry:
    titles: list[SessionTitle]
    assigned: set[SessionTitle]

    def __init__(self):
        self.titles: list[SessionTitle] = [
            TitleMostNat1(),
            TitleMostNat20(),
            TitleConsistentRoller(),
            TitleHeavyHitter(),
            TitleWeakHitter(),
        ]
        self.assigned = set()

    def assign_title(self, stats: UserSessionDiceStats, all_session_stats: dict[int, UserSessionStats]) -> SessionTitle | None:
        best_title = None
        highest_score = 0.0

        for title in self.titles:
            if title in self.assigned:
                continue  # Don't re-evaluate already assigned titles.

            score = title.evaluate(stats, all_session_stats)
            if score > highest_score:
                highest_score = score
                best_title = title

        if best_title:
            self.assigned.add(best_title)
        return best_title


# TITLES
# d20 check related titles
class TitleMostNat1(SessionTitle):
    name = "Bad Dice Day"
    description = "Rolled the most Natural 1s this session."

    def evaluate(self, stats: UserSessionDiceStats, all_session_stats: dict[int, UserSessionStats]) -> float:
        if stats.nat1_count == 0:
            return 0

        max_nat1s = max(stat.dice.nat1_count for _, stat in all_session_stats.items())
        if stats.nat1_count == max_nat1s:
            return float(stats.nat1_count)
        return 0


class TitleMostNat20(SessionTitle):
    name = "Lucky Hand"
    description = "Rolled the most Natural 20s this session."

    def evaluate(self, stats: UserSessionDiceStats, all_session_stats: dict[int, UserSessionStats]) -> float:
        if stats.nat20_count == 0:
            return 0

        max_nat20s = max(stat.dice.nat20_count for _, stat in all_session_stats.items())
        if stats.nat20_count == max_nat20s:
            return float(stats.nat20_count)
        return 0


class TitleConsistentRoller(SessionTitle):
    name = "Reliable"
    description = "Maintained an average d20 roll of 14 or higher."

    def evaluate(self, stats: UserSessionDiceStats, all_session_stats: dict[int, UserSessionStats]) -> float:
        # Require at least 5 rolls, to prevent flukes.
        if len(stats.d20_totals) >= 5 and stats.average_d20 >= 14:
            return float(stats.average_d20)
        return 0


# Damage related titles
class TitleHeavyHitter(SessionTitle):
    name = "The Juggernaut"
    description = "Dealt the highest total damage across the entire session."

    def evaluate(self, stats: UserSessionDiceStats, all_session_stats: dict[int, UserSessionStats]) -> float:
        user_total_dmg = sum(stats.damage_totals)
        if user_total_dmg == 0:
            return 0

        max_dmg = max(sum(s.dice.damage_totals) for s in all_session_stats.values())
        if user_total_dmg == max_dmg:
            return float(user_total_dmg)
        return 0


class TitleWeakHitter(SessionTitle):
    name = "Suboptimal Build"
    description = "Dealt the least amount of damage across the entire session."

    def evaluate(self, stats: UserSessionDiceStats, all_session_stats: dict[int, UserSessionStats]) -> float:
        user_total_dmg = sum(stats.damage_totals)
        if user_total_dmg == 0:
            return 0

        min_dmg = min(sum(s.dice.damage_totals) for s in all_session_stats.values())
        if user_total_dmg == min_dmg:
            return float(user_total_dmg)
        return 0
