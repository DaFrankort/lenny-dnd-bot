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


class ColorSelectView(discord.ui.View):
    def __init__(self, itr: discord.Interaction, result: UserColorSaveResult, is_hex: bool):
        super().__init__()
        self.result = result
        self.is_hex = is_hex
        user_color = UserColor.get(itr)
        for color in result.color:
            disabled = user_color == color
            self.add_item(ColorButton(color, result, is_hex, disabled))


class ColorButton(discord.ui.Button["ColorSelectView"]):
    def __init__(self, color: int, result: UserColorSaveResult, is_hex: bool, disabled: bool):
        super().__init__(style=discord.ButtonStyle.gray, label=UserColor.to_name(color), disabled=disabled)
        self.color = color
        self.result = result
        self.is_hex = is_hex

    async def callback(self, interaction: discord.Interaction):
        UserColor.add(interaction, self.color)
        embed = ColorSetEmbed(
            itr=interaction,
            result=self.result,
            is_hex=self.is_hex,
            selected_color=self.color,
        )
        await interaction.response.edit_message(embed=embed, view=embed.view, attachments=[embed.file])


class ColorSetEmbed(UserActionEmbed):
    is_hex: bool
    file: discord.File
    view: ColorSelectView | None

    def __init__(
        self,
        itr: discord.Interaction,
        result: UserColorSaveResult,
        is_hex: bool,
        selected_color: int | None = None,
    ):
        self.is_hex = is_hex
        color = selected_color or result.color[0]
        self.file = get_palette_image(color)

        descriptions: list[str] = []
        if self.is_hex:
            descriptions.append(f"``{UserColor.to_hex(result.old_color)}`` => ``{UserColor.to_hex(color)}``")
        else:
            ro, go, bo = UserColor.to_rgb(result.old_color)
            rn, gn, bn = UserColor.to_rgb(color)
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

        if len(result.color) > 1:
            self.view = ColorSelectView(itr, result, is_hex)
