from discord import app_commands
import discord

from i18n import t
from logger import log_cmd
from token_gen import (
    AlignH,
    AlignV,
    generate_token_filename,
    generate_token_image,
    generate_token_url_filename,
    generate_token_variants,
    image_to_bytesio,
    open_image,
    open_image_url,
)

TokenGenHorAlignmentChoices = [
    app_commands.Choice(name="Left", value=AlignH.LEFT.value),
    app_commands.Choice(name="Center", value=AlignH.CENTER.value),
    app_commands.Choice(name="Right", value=AlignH.RIGHT.value),
]

TokenGenVerAlignmentChoices = [
    app_commands.Choice(name="Top", value=AlignV.TOP.value),
    app_commands.Choice(name="Center", value=AlignV.CENTER.value),
    app_commands.Choice(name="Bottom", value=AlignV.BOTTOM.value),
]


class TokenGenCommand(discord.app_commands.Command):
    name = t("commands.tokengen.name")
    description = t("commands.tokengen.desc")

    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.description,
            callback=self.callback,
        )

    @app_commands.describe(
        image="The image to turn into a token.",
        frame_hue="Hue shift to apply to the token-frame (Gold: 0 | Red: -30 | Blue: 180 | Green: 80).",
        h_alignment="Horizontal alignment for the token image.",
        v_alignment="Vertical alignment for the token image.",
        variants="Create many tokens with label-numbers.",
    )
    @app_commands.choices(
        h_alignment=TokenGenHorAlignmentChoices,
        v_alignment=TokenGenVerAlignmentChoices,
    )
    async def callback(
        self,
        itr: discord.Interaction,
        image: discord.Attachment,
        frame_hue: app_commands.Range[int, -360, 360] = 0,
        h_alignment: str = AlignH.CENTER.value,
        v_alignment: str = AlignV.CENTER.value,
        variants: app_commands.Range[int, 0, 10] = 0,
    ):
        log_cmd(itr)

        if not image.content_type.startswith("image"):
            await itr.response.send_message(
                "❌ Attachment must be an image! ❌",
                ephemeral=True,
            )
            return

        await itr.response.defer()
        img = await open_image(image)

        if img is None:
            await itr.followup.send(
                "❌ Could not process image, please try again later or with another image. ❌",
            )
            return

        token_image = generate_token_image(img, frame_hue, h_alignment, v_alignment)
        if variants != 0:
            await itr.followup.send(
                files=generate_token_variants(
                    token_image=token_image, filename_seed=image, amount=variants
                )
            )
            return

        await itr.followup.send(
            file=discord.File(
                fp=image_to_bytesio(token_image),
                filename=generate_token_filename(image),
            )
        )


class TokenGenUrlCommand(discord.app_commands.Command):
    name = t("commands.tokengenurl.name")
    description = t("commands.tokengenurl.desc")

    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.description,
            callback=self.callback,
        )

    @app_commands.describe(
        url="The image-url to generate a token from.",
        frame_hue="Hue shift to apply to the token-frame (Gold: 0 | Red: -30 | Blue: 180 | Green: 80).",
        h_alignment="Horizontal alignment for the token image.",
        v_alignment="Vertical alignment for the token image.",
        variants="Create many tokens with label-numbers.",
    )
    @app_commands.choices(
        h_alignment=TokenGenHorAlignmentChoices,
        v_alignment=TokenGenVerAlignmentChoices,
    )
    async def callback(
        self,
        itr: discord.Interaction,
        url: str,
        frame_hue: app_commands.Range[int, -360, 360] = 0,
        h_alignment: str = AlignH.CENTER.value,
        v_alignment: str = AlignV.CENTER.value,
        variants: app_commands.Range[int, 0, 10] = 0,
    ):
        log_cmd(itr)

        if not url.startswith("http"):  # TODO properly validate urls
            await itr.response.send_message(
                f"❌ Not a valid URL: '{url}' ❌",
                ephemeral=True,
            )
            return

        await itr.response.defer()
        img = await open_image_url(url)

        if img is None:
            await itr.response.send_message(
                "❌ Could not process image, please provide a valid image-URL. ❌",
            )
            return

        token_image = generate_token_image(img, frame_hue, h_alignment, v_alignment)
        if variants != 0:
            await itr.followup.send(
                files=generate_token_variants(
                    token_image=token_image, filename_seed=url, amount=variants
                )
            )
            return

        await itr.followup.send(
            file=discord.File(
                fp=image_to_bytesio(token_image),
                filename=generate_token_url_filename(url),
            )
        )
