import typing
from unittest.mock import MagicMock

import d100
import d100.ast.dice
import d100.utils.find
import discord
import pytest
from d100.roll import SingleRollResult
from mocking import MockGuild, MockInteraction, MockMember, MockUser

from logic.roll import Advantage, MultiRollResult
from logic.roll import roll as roll_dice
from logic.session.stats import GlobalSessionStats, SessionStats
from logic.session.titles import TitleMostRollsDone
from logic.session.types import UserSessionDiceStats, UserSessionStats


def create_mock_single_roll(expr: str = "1d20", sides: int = 20, force: int | list[int] | None = None) -> SingleRollResult:
    result = d100.roll(expr)

    if force is not None:
        count = len(force) if isinstance(force, list) else 1
        ast = d100.utils.find.find_dice(result.roll.ast, count, sides)
        dice = typing.cast(d100.ast.dice.Dice, result.roll.roll.find_from_ast(ast))
        if isinstance(force, list):
            for die, value in zip(dice.dice, force, strict=True):
                die.set_value(value)
        else:
            dice.dice[0].values.append(force)

    return result.roll


def create_mock_multi_roll_result(
    expression: str = "1d20",
    advantage: Advantage = Advantage.NORMAL,
    warnings: list[str] | None = None,
    rolls: list[SingleRollResult] | None = None,
    rolls_lose_1: list[SingleRollResult] | None = None,
    rolls_lose_2: list[SingleRollResult] | None = None,
) -> MultiRollResult:
    result = MagicMock(spec=MultiRollResult)
    result.expression = expression
    result.advantage = advantage
    result.warnings = warnings or []
    result.rolls = rolls or [create_mock_single_roll(expr=expression)]
    result.rolls_lose_1 = rolls_lose_1 or []
    result.rolls_lose_2 = rolls_lose_2 or []

    return result


class TestSessionStats:
    def test_empty_stats_do_not_divide_by_zero(self):
        stats = UserSessionDiceStats()

        assert stats.average_rolled_d20 == 0
        assert stats.average_kept_d20 == 0
        assert stats.average_dmg == 0
        assert stats.advantage_percentage == 0
        assert stats.disadvantage_percentage == 0

    def test_add_d20_rolls_and_criticals(self):
        """Ensures Natural 20s, Natural 1s, and regular d20 rolls are recorded properly."""
        stats = UserSessionDiceStats()

        roll_nat20 = create_mock_multi_roll_result("1d20", rolls=[create_mock_single_roll("1d20", 20, 20)])
        roll_nat1 = create_mock_multi_roll_result("1d20", rolls=[create_mock_single_roll("1d20", 20, 1)])
        roll_dirty = create_mock_multi_roll_result("1d20", rolls=[create_mock_single_roll("1d20+3", 20, 17)])
        roll_norm = create_mock_multi_roll_result("1d20", rolls=[create_mock_single_roll("1d20", 20, 10)])

        stats.add(roll_nat20)
        stats.add(roll_nat1)
        stats.add(roll_dirty)
        stats.add(roll_norm)

        assert stats.nat20_count == 1
        assert stats.nat1_count == 1
        assert stats.dirty20_count == 1
        assert stats.kept_nat20_count == 1
        assert stats.kept_nat1_count == 1
        assert stats.kept_dirty20_count == 1
        assert len(stats.rolled_d20_totals) == 4
        assert len(stats.kept_d20_totals) == 4
        assert stats.average_kept_d20 == 12  # (20 + 1 + 20 + 10) // 4 = 12

    def test_critical_counts_only_include_kept_rolls(self):
        stats = UserSessionDiceStats()
        result = create_mock_multi_roll_result(
            expression="1d20",
            rolls=[create_mock_single_roll(force=20)],
            rolls_lose_1=[create_mock_single_roll(force=1)],
            rolls_lose_2=[create_mock_single_roll("1d20+3", force=17)],
        )

        stats.add(result)

        assert stats.nat20_count == 1
        assert stats.nat1_count == 1
        assert stats.dirty20_count == 1
        assert stats.kept_nat20_count == 1
        assert stats.kept_nat1_count == 0
        assert stats.kept_dirty20_count == 0

    def test_add_multiple_d20_from_single_expression(self):
        stats = UserSessionDiceStats()
        result = create_mock_multi_roll_result(
            expression="2d20",
            rolls=[create_mock_single_roll("2d20", 20, [8, 15])],
        )

        stats.add(result)

        assert stats.rolled_d20_totals == [8, 15]
        assert stats.average_rolled_d20 == 11

    def test_ignore_rolls_with_warnings(self):
        stats = UserSessionDiceStats()
        roll_with_warn = create_mock_multi_roll_result("1d20", warnings=["Invalid operator"])

        stats.add(roll_with_warn)

        assert len(stats.kept_d20_totals) == 0
        assert len(stats.rolled_d20_totals) == 0
        assert stats.total_dice_rolled == 0

    def test_count_discarded_multi_roll_dice(self):
        stats = UserSessionDiceStats()
        result = create_mock_multi_roll_result(
            expression="1d20",
            advantage=Advantage.ELVEN_ACCURACY,
            rolls=[create_mock_single_roll(force=18), create_mock_single_roll(force=16)],
            rolls_lose_1=[create_mock_single_roll(force=7), create_mock_single_roll(force=4)],
            rolls_lose_2=[create_mock_single_roll(force=12), create_mock_single_roll(force=2)],
        )

        stats.add(result)

        assert stats.rolled_dice[20] == 6
        assert stats.rolled_d20_totals == [18, 16, 7, 4, 12, 2]
        assert stats.kept_d20_totals == [18, 16]
        assert stats.average_rolled_d20 == 9
        assert stats.average_kept_d20 == 17
        assert stats.nat1_count == 0

    def test_single_roll_records_all_advantage_dice_and_kept_result(self):
        stats = UserSessionDiceStats()
        result = MagicMock()
        result.expression = "1d20"
        result.advantage = Advantage.ELVEN_ACCURACY
        result.result.warnings = []
        result.result.total = 17
        result.result.rolls = [
            create_mock_single_roll(force=5),
            create_mock_single_roll(force=17),
            create_mock_single_roll(force=12),
        ]

        stats.add(result)

        assert stats.rolled_d20_totals == [5, 17, 12]
        assert stats.kept_d20_totals == [17]

    @pytest.mark.parametrize(("expression", "kept_count"), [("5d20", 5), ("5d20kh1", 1)])
    def test_multi_d20_expression_tracks_each_die(self, expression: str, kept_count: int):
        result = roll_dice(expression)

        stats = UserSessionDiceStats()
        stats.add(result)

        assert stats.rolled_dice[20] == 5
        assert len(stats.rolled_d20_totals) == 5
        assert len(stats.kept_d20_totals) == kept_count
        assert all(value in stats.rolled_d20_totals for value in stats.kept_d20_totals)
        if kept_count == 5:
            assert stats.kept_d20_totals == stats.rolled_d20_totals

    def test_ignore_d100_and_percentile_rolls(self):
        stats = UserSessionDiceStats()
        roll_d100 = create_mock_multi_roll_result("1d100", rolls=[create_mock_single_roll("1d100", 100, 50)])

        stats.add(roll_d100)

        assert len(stats.rolled_d20_totals) == 0
        assert len(stats.kept_d20_totals) == 0
        assert len(stats.damage_totals) == 0
        assert stats.rolled_dice.get(100) == 1

    def test_damage_tracking_and_averages(self):
        stats = UserSessionDiceStats()

        dmg1 = create_mock_multi_roll_result("1d8+3", rolls=[create_mock_single_roll("1d8+3", 8, 8)])
        dmg2 = create_mock_multi_roll_result("1d8+3", rolls=[create_mock_single_roll("1d8+3", 8, 2)])

        stats.add(dmg1)
        stats.add(dmg2)

        assert stats.damage_totals == [11, 5]
        assert stats.average_dmg == 8
        assert stats.most_used_die_type == (8, 2)

    def test_main_character_title_uses_total_dice_rolled(self):
        bill = UserSessionStats()
        bill.dice.rolled_dice = {20: 200}
        bob = UserSessionStats()
        bob.dice.rolled_dice = {20: 130}

        all_session_stats = {1: bill, 2: bob}
        title = TitleMostRollsDone()

        assert title.evaluate(bill.dice, all_session_stats) == 200.0
        assert title.evaluate(bob.dice, all_session_stats) == 0.0


class TestGlobalSessionStats:
    @pytest.fixture
    def member(self) -> MockMember:
        """Helper to create a MockMember attached to a mocked voice channel."""
        member = MockMember(MockUser("VoiceUser"), MockGuild(123), admin=False)

        voice_channel = MagicMock(spec=discord.VoiceChannel)
        voice_channel.id = 321
        voice_channel.members = [member]

        voice_state = MagicMock(spec=discord.VoiceState)
        voice_state.channel = voice_channel

        member.voice = voice_state
        return member

    def test_start_and_get_session_success(self, member: MockMember):
        """Tests starting a session for a voice channel and retrieving it."""
        global_stats = GlobalSessionStats()
        itr = MockInteraction(user=member)

        session = global_stats.start(itr)

        assert isinstance(session, SessionStats)
        assert global_stats.get(itr) is session

    def test_start_duplicate_session_raises_error(self, member: MockMember):
        """Ensures starting two sessions in the same voice channel raises KeyError."""
        global_stats = GlobalSessionStats()
        itr = MockInteraction(user=member)

        global_stats.start(itr)

        with pytest.raises(ValueError):
            global_stats.start(itr)

    def test_stop_empty_session_raises_error(self, member: MockMember):
        """Ensures starting two sessions in the same voice channel raises KeyError."""
        global_stats = GlobalSessionStats()
        itr = MockInteraction(user=member)

        with pytest.raises(KeyError):
            global_stats.stop(itr)
