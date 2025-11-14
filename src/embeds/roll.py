import discord

from embeds.embed import UserActionEmbed
from logic.roll import Advantage, MultiRollResult, RollResult, SingleRollResult


class RollEmbed(UserActionEmbed):
    def __init__(
        self,
        itr: discord.Interaction,
        result: RollResult,
        reason: str | None,
        reroll: bool = False,
    ):
        title_suffix = ""
        if result.advantage == Advantage.Advantage:
            title_suffix = " with advantage"
        elif result.advantage == Advantage.Disadvantage:
            title_suffix = " with disadvantage"

        if reroll:
            title = f"Re-rolling {result.expression}{title_suffix}!"
        else:
            title = f"Rolling {result.expression}{title_suffix}!"

        if reason is None:
            reason = "Result"

        descriptions: list[str] = []

        if not result.roll.contains_dice:
            descriptions.append("⚠️ Expression contains no dice. ⚠️")

        for roll in result.rolls:
            descriptions.append(f"- `{roll.expression} -> {roll.total}`")

        roll = result.roll
        descriptions.append("")
        descriptions.append(f"🎲 **{reason}: {roll.total}**")

        if roll.is_natural_twenty:
            descriptions.append("🎯 **Critical Hit!**")
        if roll.is_natural_one:
            descriptions.append("💀 **Critical Fail!**")
        if roll.is_dirty_twenty:
            descriptions.append("⚔️  **Dirty 20!**")

        description = "\n".join(descriptions)
        if len(description) > 1024:
            description = "⚠️ Message too long, try sending a shorter expression!"

        super().__init__(itr, title, description)


class MultiRollEmbed(UserActionEmbed):
    def __init__(
        self,
        itr: discord.Interaction,
        result: MultiRollResult,
        reason: str | None,
        reroll: bool = False,
    ):
        title_suffix = ""
        if result.advantage == Advantage.Advantage:
            title_suffix = " with advantage"
        elif result.advantage == Advantage.Disadvantage:
            title_suffix = " with disadvantage"

        if reroll:
            title = f"Re-rolling {result.expression} multiple times{title_suffix}!"
        else:
            title = f"Rolling {result.expression} multiple times{title_suffix}!"

        if reason is None:
            reason = "Total"

        description = ""
        if not result.rolls[0].contains_dice:
            description = "⚠️ Expression contains no dice. ⚠️"

        winning_result = self._get_roll_list(result.rolls, False)
        losing_result = self._get_roll_list(result.rolls_lose, True)
        footer = f"\n🎲 **{reason}: {result.total}**"

        if len(winning_result) > 1024:
            super().__init__(itr, title, "⚠️ Message too long, try sending a shorter expression!")
            return

        super().__init__(itr, title, description)
        if losing_result:
            self.add_field(name="", value=losing_result, inline=True)
        self.add_field(name="", value=winning_result, inline=True)
        self.add_field(name="", value=footer, inline=False)

    def _get_roll_list(self, rolls: list[SingleRollResult], strike_through: bool = False) -> str:
        results: list[str] = []
        for roll in rolls:
            roll_message = f"`{roll.expression} -> {roll.total}`"
            if strike_through:
                roll_message = f"~~{roll_message}~~"

            if roll.is_natural_twenty:
                roll_message += " 🎯"
            elif roll.is_natural_one:
                roll_message += " 💀"
            elif roll.is_dirty_twenty:
                roll_message += " ⚔️"
            results.append(roll_message)
        return "\n".join(results)
