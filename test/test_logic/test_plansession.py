import datetime

import pytest
from mocking import MockInteraction

from logic.plansession import get_week_choice_name, in_weeks_autocomplete


def test_get_week_choice_name():
    today = datetime.date(2026, 11, 24)

    assert get_week_choice_name(0, today) == "This week"
    assert get_week_choice_name(1, today) == "Next week (30 Nov)"


@pytest.mark.asyncio
async def test_in_weeks_autocomplete():
    interaction = MockInteraction()

    choices = await in_weeks_autocomplete(interaction, "next")
    assert len(choices) == 1
    assert choices[0].value == 1
    assert choices[0].name.startswith("Next week (")

    choices = await in_weeks_autocomplete(interaction, "48")
    assert len(choices) == 1
    assert choices[0].value == 48
    assert choices[0].name.startswith("In 48 weeks (")

    choices = await in_weeks_autocomplete(interaction, "")
    assert len(choices) == 25
    assert choices[0].name == "This week"
