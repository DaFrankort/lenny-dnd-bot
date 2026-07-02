from abc import ABC, abstractmethod

from logic.session.types import UserSessionDiceStats, UserSessionStats


class SessionTitle(ABC):
    name: str
    description: str
    weight: float = 1.0

    @abstractmethod
    def _evaluate(self, stats: UserSessionDiceStats, all_session_stats: dict[int, UserSessionStats]) -> float:
        """
        Calculates an unweighted score to represent how well the user qualifies for this title.
        Do not use the title's weight in evaluation, this is applied in the main evaluate() method.
        """

        raise NotImplementedError(f"The title '{self.name}' can not be evaluated yet.")

    def evaluate(self, stats: UserSessionDiceStats, all_session_stats: dict[int, UserSessionStats]) -> float:
        """
        Returns weighted score representing how well the user qualifies for this title.
        Returns 0 or negative if they don't qualify at all.

        A title's weight can be adjusted to finetune how easy it is to receive this title.
        """

        return self._evaluate(stats, all_session_stats) * self.weight


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
            TitleAdvantage(),
            TitleDisadvantage(),
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
    name = "The Murphy's Law Enthusiast"
    description = "Rolled the most Natural 1s this session."
    weight = 5.0

    def _evaluate(self, stats: UserSessionDiceStats, all_session_stats: dict[int, UserSessionStats]) -> float:
        if stats.nat1_count == 0:
            return 0

        max_nat1s = max(stat.dice.nat1_count for _, stat in all_session_stats.items())
        if stats.nat1_count == max_nat1s:
            return float(stats.nat1_count)
        return 0


class TitleMostNat20(SessionTitle):
    name = "The Weighted Dice User"
    description = "Rolled the most Natural 20s this session."
    weight = 5.0

    def _evaluate(self, stats: UserSessionDiceStats, all_session_stats: dict[int, UserSessionStats]) -> float:
        if stats.nat20_count == 0:
            return 0

        max_nat20s = max(stat.dice.nat20_count for _, stat in all_session_stats.items())
        if stats.nat20_count == max_nat20s:
            return float(stats.nat20_count)
        return 0


class TitleConsistentRoller(SessionTitle):
    name = "The Ol' Reliable"
    description = "Maintained an average d20 roll of 14 or higher."

    def _evaluate(self, stats: UserSessionDiceStats, all_session_stats: dict[int, UserSessionStats]) -> float:
        # Require at least 5 rolls, to prevent flukes.
        if len(stats.d20_totals) >= 5 and stats.average_d20 >= 14:
            return float(stats.average_d20)
        return 0


# Damage related titles
class TitleHeavyHitter(SessionTitle):
    name = "The Min-Maxxer"
    description = "Dealt the highest total damage across the entire session."
    weight = 0.7

    def _evaluate(self, stats: UserSessionDiceStats, all_session_stats: dict[int, UserSessionStats]) -> float:
        user_total_dmg = sum(stats.damage_totals)
        if user_total_dmg == 0:
            return 0

        max_dmg = max(sum(s.dice.damage_totals) for s in all_session_stats.values())
        if user_total_dmg == max_dmg:
            return float(user_total_dmg)
        return 0


class TitleWeakHitter(SessionTitle):
    name = "The Emotional Support"
    description = "Dealt the least amount of damage across the entire session."
    weight = 5.0

    def _evaluate(self, stats: UserSessionDiceStats, all_session_stats: dict[int, UserSessionStats]) -> float:
        user_total_dmg = sum(stats.damage_totals)
        if user_total_dmg == 0:
            return 0

        min_dmg = min(sum(s.dice.damage_totals) for s in all_session_stats.values())
        if user_total_dmg == min_dmg:
            return float(user_total_dmg)
        return 0


# Advantage User
class TitleAdvantage(SessionTitle):
    name = "The Crit Fisher"
    description = "Rolled with advantage more times than anyone else."
    weight = 2.0

    def _evaluate(self, stats: UserSessionDiceStats, all_session_stats: dict[int, UserSessionStats]) -> float:
        adv_count = stats.adv_count
        if adv_count == 0:
            return 0

        max_count = max(s.dice.adv_count for s in all_session_stats.values())
        if adv_count == max_count:
            return float(adv_count)
        return 0


class TitleDisadvantage(SessionTitle):
    name = "The DM's Least Favorite"
    description = "Rolled with disadvantage more times than anyone else."
    weight = 5.0

    def _evaluate(self, stats: UserSessionDiceStats, all_session_stats: dict[int, UserSessionStats]) -> float:
        dis_count = stats.dis_count
        if dis_count == 0:
            return 0

        max_count = max(s.dice.dis_count for s in all_session_stats.values())
        if dis_count == max_count:
            return float(dis_count)
        return 0
