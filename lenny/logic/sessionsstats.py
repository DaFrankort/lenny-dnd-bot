from dataclasses import dataclass

import discord
from d100 import Critical

from logic.color import UserColor
from logic.roll import Advantage, RollResult, SingleRollResult


@dataclass
class UserSessionResult:
    user: discord.Member
    color: discord.Color
    title: str
    description: str


@dataclass
class SessionResult:
    base_info: str
    users_stats: list[UserSessionResult]


class UserSessionDiceStats:
    nat20_count: int
    nat1_count: int
    dirty20_count: int
    d20_totals: list[int]

    dmg_expressions: dict[str, list[int]]

    adv_count: int
    dis_count: int

    def __init__(self):
        self.nat20_count = 0
        self.nat1_count = 0
        self.dirty20_count = 0
        self.d20_totals = []

        self.dmg_expressions = {}

        self.adv_count = 0
        self.dis_count = 0

    def add(self, result: RollResult):
        if len(result.result.warnings) > 0:
            # Rolls with warnings are not considered valid dice-rolls.
            # But often appear when users want to quickly calculate something.
            return

        self._add_advantage(result)
        for roll in result.result.rolls:
            # TODO -> maybe use different separation? Possibly 1d10red support?
            if "d20" in result.expression:
                self._add_d20(roll)
            else:
                self._add_damage_roll(roll)

    def _add_d20(self, roll: SingleRollResult):
        self.d20_totals.append(roll.total)
        if roll.crit is Critical.CRIT:
            self.nat20_count += 1
        elif roll.crit is Critical.FAIL:
            self.nat1_count += 1
        elif roll.crit is Critical.DIRTY:
            self.dirty20_count += 1

    def _add_damage_roll(self, roll: SingleRollResult):
        if roll.expr not in self.dmg_expressions:
            self.dmg_expressions[roll.expr] = []
        self.dmg_expressions[roll.expr].append(roll.total)

    def _add_advantage(self, result: RollResult):
        if result.advantage is Advantage.ADVANTAGE or result.advantage is Advantage.ELVEN_ACCURACY:
            self.adv_count += 1
            return
        if result.advantage is Advantage.DISADVANTAGE:
            self.dis_count += 1
            return

        if "2d20kh1" in result.expression or "2d20dl1" in result.expression or "1d20adv" in result.expression:
            self.adv_count += 1
        if "2d20kl1" in result.expression or "2d20dh1" in result.expression or "1d20dis" in result.expression:
            self.dis_count += 1

    @property
    def average_d20(self) -> int:
        if len(self.d20_totals) == 0:
            return 0
        return sum(self.d20_totals) // len(self.d20_totals)

    @property
    def damage_totals(self) -> list[int]:
        values: list[int] = []
        for _, totals in self.dmg_expressions.items():
            values.extend(totals)
        return values

    @property
    def average_dmg(self) -> int:
        totals = self.damage_totals
        if len(totals) == 0:
            return 0
        return sum(totals) // len(totals)

    @property
    def dice_rolled(self) -> int:
        return len(self.d20_totals) + len(self.dmg_expressions)


class UserSessionStats:
    dice: UserSessionDiceStats

    def __init__(self):
        self.dice = UserSessionDiceStats()


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
        from logic.sessiontitles import TitleRegistry

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

            user_report.append(f"- Average d20 result: ``{dice.average_d20}``")
            user_report.append(f"\n- Average damage: ``{dice.average_dmg}``")
            user_report.append(f"\n- Dice rolled: ``{dice.dice_rolled}``")

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
