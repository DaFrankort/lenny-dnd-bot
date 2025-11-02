import discord
from command import SimpleCommand, SimpleCommandGroup
from logic.tokengen import (
    AlignH,
    AlignV,
    generate_token_from_file,
    generate_token_from_url,
)
from discord.app_commands import describe, choices, Range


class TokenGenCommandGroup(SimpleCommandGroup):
    name = "tokengen"
    desc = "Create 5e.tools-style creature-tokens."

    def __init__(self):
        super().__init__()
        self.add_command(TokenGenCommand())
        self.add_command(TokenGenUrlCommand())


class TokenGenCommand(SimpleCommand):
    name = "file"
    desc = "Turn an image into a 5e.tools-style token."
    help = "Generates a token image from an image attachment."

    @describe(
        image="The image to turn into a token.",
        frame_hue="Hue shift to apply to the token-frame (Gold: 0 | Red: -30 | Blue: 180 | Green: 80).",
        h_alignment="Horizontal alignment for the token image.",
        v_alignment="Vertical alignment for the token image.",
        variants="Create many tokens with label-numbers.",
    )
    @choices(
        h_alignment=AlignH.choices(),
        v_alignment=AlignV.choices(),
    )
    async def callback(  # pyright: ignore
        self,
        itr: discord.Interaction,
        image: discord.Attachment,
        frame_hue: Range[int, -360, 360] = 0,
        h_alignment: str = AlignH.CENTER.value,
        v_alignment: str = AlignV.CENTER.value,
        variants: Range[int, 0, 10] = 0,
    ):
        self.log(itr)
        await itr.response.defer()

        h_align = AlignH(h_alignment)
        v_align = AlignV(v_alignment)
        files = await generate_token_from_file(image, frame_hue, h_align, v_align, variants)
        await itr.followup.send(files=files)


class TokenGenUrlCommand(SimpleCommand):
    name = "url"
    desc = "Turn an image url into a 5e.tools-style token."
    help = "Generates a token image from an image url."

    @describe(
        url="The image-url to generate a token from.",
        frame_hue="Hue shift to apply to the token-frame (Gold: 0 | Red: -30 | Blue: 180 | Green: 80).",
        h_alignment="Horizontal alignment for the token image.",
        v_alignment="Vertical alignment for the token image.",
        variants="Create many tokens with label-numbers.",
    )
    @choices(
        h_alignment=AlignH.choices(),
        v_alignment=AlignV.choices(),
    )
    async def callback(  # pyright: ignore
        self,
        itr: discord.Interaction,
        url: str,
        frame_hue: Range[int, -360, 360] = 0,
        h_alignment: str = AlignH.CENTER.value,
        v_alignment: str = AlignV.CENTER.value,
        variants: Range[int, 0, 10] = 0,
    ):
        self.log(itr)
        await itr.response.defer()

        h_align = AlignH(h_alignment)
        v_align = AlignV(v_alignment)
        files = await generate_token_from_url(url, frame_hue, h_align, v_align, variants)
        await itr.followup.send(files=files)
