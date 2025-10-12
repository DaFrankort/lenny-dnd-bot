import discord

from embed import UserActionEmbed
from logic.color import UserColorSaveResult, get_palette_image


class ColorShowEmbed(UserActionEmbed):
    file: discord.File

    def __init__(self, itr: discord.Interaction, color: int):
        title = f"{itr.user.display_name}'s color!"
        self.file = get_palette_image(color)

        super().__init__(itr=itr, title=title, description="")
        self.set_image(url=f"attachment://{self.file.filename}")


class ColorSetEmbed(UserActionEmbed):
    file: discord.File

    def __init__(self, itr: discord.Interaction, result: UserColorSaveResult):
        self.file = get_palette_image(result.color)
        super().__init__(
            itr=itr,
            title=f"{itr.user.display_name} set a new color!",
            description=result.description,
        )
        self.set_image(url=f"attachment://{self.file.filename}")
