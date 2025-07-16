import datetime
from discord import Poll

from utils import when


class SessionPlanPoll(Poll):
    def __init__(self, in_weeks: int):
        super().__init__(
            question=self._get_question(in_weeks),
            duration=datetime.timedelta(hours=1),  # Minimum required time is 1 hour.
            multiple=True,
        )

        self._add_date_answers(in_weeks)

    def _get_question(self, in_weeks: int):
        if in_weeks in (0, 1):
            week_phrase = when(in_weeks == 0, "this week", "next week")
        else:
            week_phrase = f"in {in_weeks} weeks"

        return f"Session {week_phrase}, which day works for you?"

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
                day_text = "Earlier"
                relative_text = None
                emoji = "⬆️"

            elif i == answer_count - 1:
                day_text = "Later"
                relative_text = None
                emoji = "⬇️"

            else:
                shift = i - today.weekday() - 1 + (in_weeks * 7)
                day_offset = when(is_this_week, i + 1, shift)
                day = today + datetime.timedelta(days=day_offset)
                day_text = day.strftime("%A %d %b")

                day_is_tomorrow = day_offset == 1
                relative_text = when(
                    day_is_tomorrow, "Tomorrow", f"In {day_offset} days"
                )
                emoji = "📅"

            if relative_text is None or in_weeks > 4:
                self.add_answer(text=day_text, emoji=emoji)
            else:
                self.add_answer(text=f"{day_text} ({relative_text})", emoji=emoji)
