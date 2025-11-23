import discord

from embeds.embed import UserActionEmbed
from logic.color import UserColor, UserColorSaveResult, get_palette_image


class ColorShowEmbed(UserActionEmbed):
    file: discord.File

    def __init__(self, itr: discord.Interaction, color: int):
        title = f"{itr.user.display_name}'s color!"
        self.file = get_palette_image(color)

        super().__init__(itr=itr, title=title, description="")
        self.set_image(url=f"attachment://{self.file.filename}")


class ColorSetEmbed(UserActionEmbed):
    is_hex: bool
    file: discord.File

    def __init__(self, itr: discord.Interaction, result: UserColorSaveResult, is_hex: bool):
        self.is_hex = is_hex
        self.file = get_palette_image(result.color)

        descriptions: list[str] = []
        if self.is_hex:
            descriptions.append(f"``{UserColor.to_hex(result.old_color)}`` => ``{UserColor.to_hex(result.color)}``")
        else:
            ro, go, bo = UserColor.to_rgb(result.old_color)
            rn, gn, bn = UserColor.to_rgb(result.color)
            descriptions.append(f"R ``{ro:03}`` => ``{rn:03}``")
            descriptions.append(f"G ``{go:03}`` => ``{gn:03}``")
            descriptions.append(f"B ``{bo:03}`` => ``{bn:03}``")
        description = "\n".join(descriptions)

        super().__init__(
            itr=itr,
            title=f"{itr.user.display_name} set a new color!",
            description=description,
        )
        self.set_image(url=f"attachment://{self.file.filename}")
