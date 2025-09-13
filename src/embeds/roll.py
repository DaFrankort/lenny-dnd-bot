import discord
from embeds2 import UserActionEmbed
from logic.roll import Advantage, ResultSpecific, RollResult


class RollEmbed(UserActionEmbed):
    ephemeral: bool

    def __init__(
        self,
        itr: discord.Interaction,
        result: RollResult,
        reason: str | None,
        is_reroll: bool = False,
    ):
        self.ephemeral = False

        if result.error is not None:
            self.ephemeral = True
            title = f"Failed to roll expression '{result.expression}'"
            description = f"❌ {result.error} ❌"
            super().__init__(itr, title, description)
            return

        prefix = "Re-rolling" if is_reroll else "Rolling"
        if result.advantage == Advantage.Advantage:
            title = f"{prefix} {result.expression} with advantage!"
        elif result.advantage == Advantage.Disadvantage:
            title = f"{prefix} {result.expression} with disadvantage!"
        else:
            title = f"{prefix} {result.expression}!"

        description = []

        if not result.contains_dice:
            description.append("⚠️ Expression contains no dice.")

        for roll in result.rolls:
            description.append(f"- `{str(roll)}` -> {roll.total}")

        if reason is None:
            reason = "Result"
        description.append("")
        description.append(f"🎲 **{reason}: {result.total}**")

        if result.specific == ResultSpecific.Nat20:
            description.append("🎯 **Critical Hit!**")
        elif result.specific == ResultSpecific.Nat1:
            description.append("💀 **Critical Fail!**")
        elif result.specific == ResultSpecific.Dirty20:
            description.append("⚔️ **Dirty 20!**")

        description = "\n".join(description)
        if len(description) > 1024:
            self.ephemeral = True
            description = "⚠️ Message too long, try sending a shorter expression!"

        super().__init__(itr, title, description)
