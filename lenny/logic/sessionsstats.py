import discord
from d20 import Advantage, Critical

from logic.roll import RollResult, SingleRollResult


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
        if len(result.warnings) > 0:
            # Rolls with warnings are not considered valid dice-rolls.
            # But often appear when users want to quickly calculate something.
            return

        self._add_advantage(result)
        for roll in result.rolls:
            # TODO -> maybe use different separation? Possibly 1d10red support?
            if "d20" in roll.expr:
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
        elif result.advantage is Advantage.DISADVANTAGE:
            self.dis_count += 1
            return

        if "2d20kh1" in result.expression or "2d20dl1" in result.expression or "adv" in result.expression:
            self.adv_count += 1
        if "2d20kl1" in result.expression or "2d20dh1" in result.expression or "dis" in result.expression:
            self.dis_count += 1

    @property
    def average_d20(self) -> int:
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

    def get_report(self, itr: discord.Interaction) -> str:
        if not itr.guild:
            raise PermissionError("Must be in a server to get a report!")

        report = "# Session Stats"
        for user_id in self.user_data:
            user = itr.guild.get_member(user_id)
            if not user:
                continue
            dice: UserSessionDiceStats = self.user_data[user_id].dice
            user_report = f"\n\n### {user.display_name}"
            user_report += f"\n- Average d20 result: ``{dice.average_d20}``"
            user_report += f"\n- Average damage: ``{dice.average_dmg}``"
            user_report += f"\n- Dice rolled: ``{dice.dice_rolled}``"
            report += user_report

        print(report)
        return report


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
        session_id = self._get_itr_id(itr)
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
