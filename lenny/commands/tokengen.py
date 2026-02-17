import os.path

import discord
from discord.app_commands import Range, choices, describe

from commands.command import BaseCommand, BaseCommandGroup
from logic.tokengen import (
    AlignH,
    AlignV,
    BackgroundType,
    generate_token_files,
    open_image_from_attachment,
    open_image_from_url,
)


class TokenGenCommandGroup(BaseCommandGroup):
    name = "tokengen"
    desc = "Create 5e.tools-style creature-tokens."

    def __init__(self):
        super().__init__()
        self.add_command(TokenGenCommand())
        self.add_command(TokenGenUrlCommand())


class TokenGenCommand(BaseCommand):
    name = "file"
    desc = "Turn an image into a 5e.tools-style token."
    help = "Generates a token image from an image attachment."

    @describe(
        image="The image to turn into a token.",
        frame_hue="Hue shift to apply to the token-frame (Gold: 0 | Red: -30 | Blue: 180 | Green: 80).",
        background_type="For transparent images; choose what type of background you'd like to apply.",
        custom_background="Custom background image to be added for transparent token. Overwrites background_type.",
        h_alignment="Horizontal alignment for the token image.",
        v_alignment="Vertical alignment for the token image.",
        variants="Create many tokens with label-numbers.",
    )
    @choices(
        background_type=BackgroundType.choices(),
        h_alignment=AlignH.choices(),
        v_alignment=AlignV.choices(),
    )
    async def handle(
        self,
        itr: discord.Interaction,
        image: discord.Attachment,
        frame_hue: Range[int, -360, 360] = 0,
        background_type: str = BackgroundType.FANCY.value,
        custom_background: discord.Attachment | None = None,
        h_alignment: str = AlignH.CENTER,
        v_alignment: str = AlignV.CENTER,
        variants: Range[int, 0, 10] = 0,
    ):
        await itr.response.defer()

        img = await open_image_from_attachment(image)
        name = os.path.splitext(image.filename)[0]
        h_align = AlignH(h_alignment)
        v_align = AlignV(v_alignment)

        if custom_background is None:
            background = BackgroundType(background_type).image
        else:
            background = await open_image_from_attachment(custom_background)

        files = generate_token_files(
            image=img,
            name=name,
            frame_hue=frame_hue,
            h_alignment=h_align,
            v_alignment=v_align,
            variants=variants,
            background=background,
        )
        await itr.followup.send(files=files)


class TokenGenUrlCommand(BaseCommand):
    name = "url"
    desc = "Turn an image url into a 5e.tools-style token."
    help = "Generates a token image from an image url."

    @describe(
        url="The image-url to generate a token from.",
        frame_hue="Hue shift to apply to the token-frame (Gold: 0 | Red: -30 | Blue: 180 | Green: 80).",
        background_type="For transparent images; choose what type of background you'd like to apply.",
        custom_background="The image-url for the custom background image to be added for transparent token. Overwrites background_type.",
        h_alignment="Horizontal alignment for the token image.",
        v_alignment="Vertical alignment for the token image.",
        variants="Create many tokens with label-numbers.",
    )
    @choices(
        background_type=BackgroundType.choices(),
        h_alignment=AlignH.choices(),
        v_alignment=AlignV.choices(),
    )
    async def handle(
        self,
        itr: discord.Interaction,
        url: str,
        frame_hue: Range[int, -360, 360] = 0,
        background_type: str = BackgroundType.FANCY.value,
        custom_background: str | None = None,
        h_alignment: str = AlignH.CENTER,
        v_alignment: str = AlignV.CENTER,
        variants: Range[int, 0, 10] = 0,
    ):
        await itr.response.defer()

        img = await open_image_from_url(url)
        url_hash = str(abs(hash(url)))

        h_align = AlignH(h_alignment)
        v_align = AlignV(v_alignment)

        if custom_background is None:
            background = BackgroundType(background_type).image
        else:
            background = await open_image_from_url(custom_background)

        files = generate_token_files(
            image=img,
            name=url_hash,
            frame_hue=frame_hue,
            h_alignment=h_align,
            v_alignment=v_align,
            variants=variants,
            background=background,
        )
        await itr.followup.send(files=files)
