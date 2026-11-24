import datetime

import discord

from logic.plansession import get_week_phrase
from methods import when


class SessionPlanPoll(discord.Poll):
    def __init__(self, in_weeks: int, poll_duration: int):
        super().__init__(
            question=self._get_question(in_weeks),
            duration=datetime.timedelta(hours=poll_duration),  # Minimum required time is 1 hour.
            multiple=True,
        )

        self._add_date_answers(in_weeks)

    def _get_question(self, in_weeks: int):
        week_phrase = get_week_phrase(in_weeks)
        return f"Session {week_phrase}, which days work for you?"

    def _add_date_answers(self, in_weeks: int):
        today = datetime.date.today()
        is_this_week = in_weeks == 0

        if not is_this_week:
            self.add_answer(text="Earlier", emoji="⬆️")

        for i in range(7):
            shift = i - today.weekday() + (in_weeks * 7)
            day_offset = when(is_this_week, i + 1, shift)
            day = today + datetime.timedelta(days=day_offset)
            day_text = day.strftime("%A %d %b")
            emoji = "📅"

            # Don't show relative 'in x days' text past 2 weeks, adds no value at that point.
            if in_weeks > 2:
                self.add_answer(text=day_text, emoji=emoji)
                continue

            day_is_tomorrow = day_offset == 1
            relative_text = when(day_is_tomorrow, "Tomorrow", f"In {day_offset} days")

            self.add_answer(text=f"{day_text} ({relative_text})", emoji=emoji)

        self.add_answer(text="Later", emoji="⬇️")
