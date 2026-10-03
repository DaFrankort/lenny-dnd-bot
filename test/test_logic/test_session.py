import typing
from unittest.mock import MagicMock

import d100
import d100.ast.dice
import d100.utils.crit
import d100.utils.find
import discord
import pytest
from d100.roll import SingleRollResult
from mocking import MockGuild, MockInteraction, MockMember, MockUser

from logic.roll import Advantage, MultiRollResult
from logic.session.stats import GlobalSessionStats, SessionStats
from logic.session.types import UserSessionDiceStats


def create_mock_single_roll(expr: str, sides: int, force: int | None = None) -> SingleRollResult:
    result = d100.roll(expr)

    if force:
        ast = d100.utils.find.find_dice(result.roll.ast, 1, sides)
        dice = typing.cast(d100.ast.dice.Dice, result.roll.roll.find_from_ast(ast))
        dice.dice[0].values.append(force)

        # Re-determine the crit type, as this is a constant value
        result.roll.crit = d100.utils.crit.determine_crit_type(result.roll.roll, dice)

    return result.roll


def create_mock_multi_roll_result(
    expression: str = "1d20",
    advantage: Advantage = Advantage.NORMAL,
    warnings: list[str] | None = None,
    rolls: list[SingleRollResult] | None = None,
) -> MultiRollResult:
    result = MagicMock(spec=MultiRollResult)
    result.expression = expression
    result.advantage = advantage
    result.warnings = warnings or []
    result.rolls = rolls or []

    return result


class TestSessionStats:
    def test_empty_stats_do_not_divide_by_zero(self):
        stats = UserSessionDiceStats()

        assert stats.average_d20 == 0
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
        assert len(stats.d20_totals) == 4
        assert stats.average_d20 == 12  # (20 + 1 + 20 + 10) // 4 = 12

    def test_ignore_rolls_with_warnings(self):
        stats = UserSessionDiceStats()
        roll_with_warn = create_mock_multi_roll_result("1d20", warnings=["Invalid operator"])

        stats.add(roll_with_warn)

        assert len(stats.d20_totals) == 0
        assert stats.total_dice_rolled == 0

    def test_ignore_d100_and_percentile_rolls(self):
        stats = UserSessionDiceStats()
        roll_d100 = create_mock_multi_roll_result("1d100", rolls=[create_mock_single_roll("1d100", 100, 50)])

        stats.add(roll_d100)

        assert len(stats.d20_totals) == 0
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
