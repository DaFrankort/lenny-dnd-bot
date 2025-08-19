import datetime
import discord

from i18n import t
from methods import when


class SessionPlanPoll(discord.Poll):
    def __init__(self, in_weeks: int, poll_duration: int):
        super().__init__(
            question=self._get_question(in_weeks),
            duration=datetime.timedelta(
                hours=poll_duration
            ),  # Minimum required time is 1 hour.
            multiple=True,
        )

        self._add_date_answers(in_weeks)

    def _get_question(self, in_weeks: int):
        if in_weeks in (0, 1):
            week_phrase = when(
                in_weeks == 0, t("common.this_week"), t("common.next_week")
            )
        else:
            week_phrase = t("common.in_x_weeks", in_weeks)

        return t("common.week_x_question", week_phrase)

    def _add_date_answers(self, in_weeks: int):
        today = datetime.date.today()
        is_this_week = in_weeks == 0
        answer_count_thisweek = (
            6 - today.weekday() + 1
        )  # Remaining days of the week + 'later' option
        answer_count = when(
            is_this_week, answer_count_thisweek, 9
        )  # 9 => 7 days + later/earlier options

        for i in range(answer_count):
            if i == 0 and not is_this_week:
                day_text = t("common.earlier")
                relative_text = None
                emoji = "⬆️"

            elif i == answer_count - 1:
                day_text = t("common.later")
                relative_text = None
                emoji = "⬇️"

            else:
                shift = i - today.weekday() - 1 + (in_weeks * 7)
                day_offset = when(is_this_week, i + 1, shift)
                day = today + datetime.timedelta(days=day_offset)
                day_text = day.strftime("%A %d %b")

                day_is_tomorrow = day_offset == 1
                relative_text = when(
                    day_is_tomorrow,
                    t("common.tomorrow"),
                    t("common.in_x_days", day_offset),
                )
                emoji = "📅"

            if relative_text is None or in_weeks > 4:
                self.add_answer(text=day_text, emoji=emoji)
                continue

            self.add_answer(text=f"{day_text} ({relative_text})", emoji=emoji)


class PlanSessionCommand(discord.app_commands.Command):
    name = t("commands.plansession.name")
    description = t("commands.plansession.desc")

    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.description,
            callback=self.callback,
        )

    @discord.app_commands.describe(
        in_weeks=t("commands.plansession.args.in_weeks"),
        poll_duration=t("commands.plansession.args.poll_duration"),
    )
    async def callback(
        self,
        itr: discord.Interaction,
        in_weeks: discord.app_commands.Range[int, 0, 48],
        poll_duration: discord.app_commands.Range[int, 1, 168] = 24,
    ):
        poll = SessionPlanPoll(in_weeks, poll_duration)
        await itr.response.send_message(poll=poll)
