import discord

from embeds import UserActionEmbed
from i18n import t
from logger import log_cmd
from user_colors import UserColor


class ColorCommand(discord.app_commands.Command):
    name = t("commands.color.name")
    description = t("commands.color.desc")

    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.description,
            callback=self.callback,
        )

    async def callback(self, itr: discord.Interaction, hex_color: str = ""):
        log_cmd(itr)
        if hex_color == "":
            removed = UserColor.remove(itr)
            message = (
                "❌ Cleared user-defined color. ❌"
                if removed
                else "⚠️ You have not yet set a color. ⚠️"
            )
            await itr.response.send_message(message, ephemeral=True)
            return

        if not UserColor.validate(hex_color):
            await itr.response.send_message(
                "⚠️ Invalid hex value: Must be 6 valid hexadecimal characters (0-9, A-F), optionally starting with a # symbol. (eg. ff00ff / #ff00ff) ⚠️",
                ephemeral=True,
            )
            return

        old_color = f"#{UserColor.get(itr):06X}"
        color = UserColor.parse(hex_color)
        UserColor.save(itr, color)
        await itr.response.send_message(
            embed=UserActionEmbed(
                itr=itr,
                title=f"{itr.user.display_name} set a new color!",
                description=f"``{old_color.upper()}`` => ``#{hex_color.upper()}``",
            ),
            ephemeral=True,
        )
