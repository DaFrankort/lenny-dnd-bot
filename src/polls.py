import datetime
from discord import Poll, PollLayoutType


class SessionPlanPoll(Poll):
    def __init__(self, in_weeks: int):
        super().__init__(
            question=self._get_question(in_weeks),
            duration=datetime.timedelta(hours=1),  # Minimum required time is 1 hour.
            multiple=True,
        )

        self._add_date_answers(in_weeks)

    def _get_question(self, in_weeks: int):
        if in_weeks == 0:
            return "Session this week, which day works for you?"
        elif in_weeks == 1:
            return "Session next week, which day works for you?"
        return f"Session in {in_weeks} weeks, which day works for you?"

    def _add_date_answers(self, in_weeks: int):
        today = datetime.date.today()
        if in_weeks == 0:
            answer_count = (6 - today.weekday()) + 1  # +1 for 'later' option
        else:
            answer_count = 7 + 2  # 7 days + earlier/later option

        for i in range(answer_count):
            relative_text = None

            if i == 0 and in_weeks != 0:
                day_text = "Earlier"
                emoji = "⬆️"
            elif i == answer_count - 1:
                day_text = "Later"
                emoji = "⬇️"
            else:
                if in_weeks == 0:
                    day_offset = i + 1  # Start from tomorrow
                else:
                    day_offset = (
                        i - today.weekday() - 1 + (in_weeks * 7)
                    )  # Shift to monday, with offset to account for Earlier option

                day = today + datetime.timedelta(days=day_offset)
                day_text = day.strftime("%A %d %b")
                relative_text = (
                    f"In {day_offset} days" if day_offset != 1 else "Tomorrow"
                )
                emoji = "📅"

            if relative_text is None or in_weeks > 4:
                self.add_answer(text=day_text, emoji=emoji)
            else:
                self.add_answer(text=f"{day_text} ({relative_text})", emoji=emoji)
