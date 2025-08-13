import logging
import os
import re
import discord
from discord import app_commands
from discord import Interaction
from dotenv import load_dotenv
from help import HelpEmbed
from i18n import t

from dice import DiceExpression, DiceExpressionCache, DiceRollMode
from dnd import DNDData, DNDObject, Gender
from embeds import (
    NoResultsFoundEmbed,
    MultiDNDSelectView,
    SimpleEmbed,
    UserActionEmbed,
)
from initiative import (
    InitiativeEmbed,
    InitiativeTracker,
)
from polls import SessionPlanPoll
from search import SearchEmbed, search_from_query
from shortcuts import ShortcutEmbed
from stats import Stats
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
from user_colors import UserColor
from voice_chat import VC, SoundType, Sounds


class Bot(discord.Client):
    tree: app_commands.CommandTree
    token: str
    guild_id: int | None
    data: DNDData
    initiatives: InitiativeTracker
    voice_enabled: bool

    def __init__(self, voice: bool = True):
        load_dotenv()
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(
            intents=intents,
            status=discord.Status.do_not_disturb,  # Set to online in on_ready
        )

        self.tree = app_commands.CommandTree(self)
        self.token = os.getenv("DISCORD_BOT_TOKEN")

        guild_id = os.getenv("GUILD_ID")
        self.guild_id = int(guild_id) if guild_id is not None else None
        self.voice_enabled = voice

        self.data = DNDData()
        self.initiatives = InitiativeTracker()

    def run_client(self):
        """Starts the bot using the token stored in .env"""
        # log_handler set to None, as a handler is already added in main.py
        super().run(self.token, log_handler=None)

    async def on_ready(self):
        """Runs automatically when the bot is online"""
        logging.info("Initializing")
        logging.info(f"Logged in as {self.user} (ID: {self.user.id})")

        self._register_commands()
        await self._attempt_sync_guild()
        await self.tree.sync()
        Sounds.init_folders()
        if self.voice_enabled:
            VC.check_ffmpeg()
        else:
            VC.disable_vc()

        await self.change_presence(
            activity=discord.CustomActivity(name="Rolling d20s!"),
            status=discord.Status.online,
        )
        logging.info("Finished initialization")

    async def _attempt_sync_guild(self):
        guild = discord.utils.get(self.guilds, id=self.guild_id)
        if guild is None:
            logging.warning("Could not find guild, check .env for GUILD_ID")
        else:
            await self.tree.sync(guild=guild)
            logging.info(f"Connected to guild: {guild.name} (ID: {guild.id})")

    def _register_commands(self):
        logging.info("Registered slash-commands")

        #
        # HELPER FUNCTIONS
        #

        def log_cmd(itr: Interaction):
            """Helper function to log user's command-usage in the terminal"""
            try:
                criteria = [f"[{k}={v}]" for k, v in vars(itr.namespace).items()]
            except Exception:
                criteria = []
            criteria_text = " ".join(criteria)

            logging.info(f"{itr.user.name} => /{itr.command.name} {criteria_text}")

        async def send_DNDObject_lookup_result(
            itr: Interaction, label: str, found: list[DNDObject], name: str
        ):
            logging.debug(f"{label.upper()}: Found {len(found)} for '{name}'")

            if len(found) == 0:
                embed = NoResultsFoundEmbed(label, name)
                await itr.response.send_message(embed=embed, ephemeral=True)

            elif len(found) > 1:
                view = MultiDNDSelectView(name, found)
                await itr.response.send_message(view=view, ephemeral=True)

            else:
                embed = found[0].get_embed()
                view = embed.view
                if view:
                    await itr.response.send_message(embed=embed, view=view)
                    return
                await itr.response.send_message(embed=embed)

        def _get_diceroll_shortcut(
            itr: Interaction, diceroll: str, reason: str | None
        ) -> tuple[str, str | None]:
            shortcuts = DiceExpressionCache.get_user_shortcuts(itr)
            if not shortcuts:
                return diceroll, reason

            parts = re.split(r"([+\-*/()])", diceroll)
            shortcut_reason = None
            for part in parts:
                part = part.strip()

                if part in shortcuts:
                    shortcut = shortcuts[part]
                    expression = shortcut["expression"]
                    reason = shortcut["reason"]
                    diceroll = diceroll.replace(part, expression)
                    shortcut_reason = reason

            return diceroll, reason or shortcut_reason

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

        GenderChoices = [
            app_commands.Choice(name="Female", value=Gender.FEMALE.value),
            app_commands.Choice(name="Male", value=Gender.MALE.value),
            app_commands.Choice(name="Other", value=Gender.OTHER.value),
        ]

        #
        # COMMANDS
        #

        @self.tree.command(
            name=t("commands.roll.name"), description=t("commands.roll.desc")
        )
        async def roll(itr: Interaction, diceroll: str, reason: str = None):
            log_cmd(itr)
            dice_notation, reason = _get_diceroll_shortcut(itr, diceroll, reason)
            expression = DiceExpression(
                dice_notation, mode=DiceRollMode.Normal, reason=reason
            )
            DiceExpressionCache.store_expression(itr, expression, diceroll)

            await itr.response.send_message(
                embed=UserActionEmbed(
                    itr=itr,
                    title=expression.title,
                    description=expression.description,
                ),
                ephemeral=expression.ephemeral,
            )
            await VC.play_dice_roll(itr, expression, reason)

        @self.tree.command(
            name=t("commands.d20.name"), description=t("commands.d20.desc")
        )
        async def d20(itr: Interaction):
            log_cmd(itr)
            expression = DiceExpression("1d20", DiceRollMode.Normal)
            await itr.response.send_message(
                embed=UserActionEmbed(
                    itr=itr,
                    title=expression.title,
                    description=expression.description,
                ),
                ephemeral=expression.ephemeral,
            )
            await VC.play_dice_roll(itr, expression)

        @self.tree.command(
            name=t("commands.advantage.name"), description=t("commands.advantage.desc")
        )
        async def advantage(itr: Interaction, diceroll: str, reason: str = None):
            log_cmd(itr)
            dice_notation, reason = _get_diceroll_shortcut(itr, diceroll, reason)
            expression = DiceExpression(
                dice_notation, DiceRollMode.Advantage, reason=reason
            )
            DiceExpressionCache.store_expression(itr, expression, diceroll)

            await itr.response.send_message(
                embed=UserActionEmbed(
                    itr=itr,
                    title=expression.title,
                    description=expression.description,
                ),
                ephemeral=expression.ephemeral,
            )
            await VC.play_dice_roll(itr, expression, reason)

        @self.tree.command(
            name=t("commands.disadvantage.name"),
            description=t("commands.disadvantage.desc"),
        )
        async def disadvantage(itr: Interaction, diceroll: str, reason: str = None):
            log_cmd(itr)
            dice_notation, reason = _get_diceroll_shortcut(itr, diceroll, reason)
            expression = DiceExpression(
                dice_notation, DiceRollMode.Disadvantage, reason=reason
            )
            DiceExpressionCache.store_expression(itr, expression, diceroll)

            await itr.response.send_message(
                embed=UserActionEmbed(
                    itr=itr,
                    title=expression.title,
                    description=expression.description,
                ),
                ephemeral=expression.ephemeral,
            )
            await VC.play_dice_roll(itr, expression, reason)

        @self.tree.context_menu(name=t("contextmenu.reroll.name"))
        async def reroll(itr: Interaction, message: discord.Message):
            log_cmd(itr)
            if message.author.id != itr.client.user.id:
                await itr.response.send_message(
                    f"❌ Only works on dice-roll messages sent by {itr.client.user.name} ❌",
                    ephemeral=True,
                )
                return

            if not message.embeds or len(message.embeds) == 0:
                await itr.response.send_message(
                    "❌ Reroll doesn't work on this message type!", ephemeral=True
                )
                return

            embed = message.embeds[0]
            title = embed.author.name or ""
            if not ("Rolling" in title or "Re-rolling" in title):
                await itr.response.send_message(
                    "❌ Message does not contain a dice-roll!", ephemeral=True
                )
                return

            dice_notation = (
                title.replace("Rolling ", "").replace("Re-rolling", "").replace("!", "")
            )
            if "disadvantage" in dice_notation:
                # Check 'disadvantage' before 'advantage', may give a false positive otherwise.
                mode = DiceRollMode.Disadvantage
                dice_notation = dice_notation.replace("with disadvantage", "")
            elif "advantage" in dice_notation:
                mode = DiceRollMode.Advantage
                dice_notation = dice_notation.replace("with advantage", "")
            else:
                mode = DiceRollMode.Normal
            dice_notation = dice_notation.strip()

            reason = None
            if "Result" not in embed.fields[0].value:
                lines = embed.fields[0].value.strip().splitlines()
                for line in lines:
                    if line.startswith("🎲") and ":" in line:
                        label = (
                            line[1:].split(":", 1)[0].strip()
                        )  # Remove 🎲 and split before colon
                        reason = label.replace("*", "")
                        break

            expression = DiceExpression(
                expression=dice_notation, mode=mode, reason=reason
            )
            expression.title = expression.title.replace("Rolling", "Re-rolling")
            DiceExpressionCache.store_expression(itr, expression, dice_notation)

            await itr.response.send_message(
                embed=UserActionEmbed(
                    itr=itr,
                    title=expression.title,
                    description=expression.description,
                ),
                ephemeral=expression.ephemeral,
            )
            await VC.play_dice_roll(itr, expression, reason)

        @roll.autocomplete("diceroll")
        @advantage.autocomplete("diceroll")
        @disadvantage.autocomplete("diceroll")
        async def autocomplete_roll_expression(
            itr: Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            return DiceExpressionCache.get_autocomplete_suggestions(itr, current)

        @roll.autocomplete("reason")
        @advantage.autocomplete("reason")
        @disadvantage.autocomplete("reason")
        async def autocomplete_roll_reason(
            itr: Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            reasons = [
                "Attack",
                "Damage",
                "Saving Throw",
                "Athletics",
                "Acrobatics",
                "Sleight of Hand",
                "Stealth",
                "Arcana",
                "History",
                "Investigation",
                "Nature",
                "Religion",
                "Animal Handling",
                "Insight",
                "Medicine",
                "Perception",
                "Survival",
                "Deception",
                "Intimidation",
                "Performance",
                "Persuasion",
                "Fire",
            ]
            filtered_reasons = [
                reason for reason in reasons if current.lower() in reason.lower()
            ]
            return [
                app_commands.Choice(name=reason, value=reason)
                for reason in filtered_reasons[:25]
            ]

        @self.tree.command(
            name=t("commands.shortcut.name"),
            description=t("commands.shortcut.desc"),
        )
        async def shortcut(itr: Interaction):
            log_cmd(itr)
            embed = ShortcutEmbed(itr)
            await itr.response.send_message(
                embed=embed, view=embed.view, ephemeral=True
            )

        @self.tree.command(
            name=t("commands.spell.name"), description=t("commands.spell.desc")
        )
        async def spell(itr: Interaction, name: str):
            log_cmd(itr)
            found = self.data.spells.get(name)
            await send_DNDObject_lookup_result(itr, "spells", found, name)

        @spell.autocomplete("name")
        async def spell_autocomplete(
            itr: discord.Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            return self.data.spells.get_autocomplete_suggestions(query=current)

        @self.tree.command(
            name=t("commands.item.name"), description=t("commands.item.desc")
        )
        async def item(itr: Interaction, name: str):
            log_cmd(itr)
            found = self.data.items.get(name)
            await send_DNDObject_lookup_result(itr, "items", found, name)

        @item.autocomplete("name")
        async def item_autocomplete(
            itr: discord.Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            return self.data.items.get_autocomplete_suggestions(query=current)

        @self.tree.command(
            name=t("commands.condition.name"),
            description=t("commands.condition.desc"),
        )
        async def condition(itr: Interaction, name: str):
            log_cmd(itr)
            found = self.data.conditions.get(name)
            await send_DNDObject_lookup_result(itr, "conditions", found, name)

        @condition.autocomplete("name")
        async def condition_autocomplete(
            itr: discord.Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            return self.data.conditions.get_autocomplete_suggestions(query=current)

        @self.tree.command(
            name=t("commands.creature.name"),
            description=t("commands.creature.desc"),
        )
        async def creature(itr: Interaction, name: str):
            log_cmd(itr)
            found = self.data.creatures.get(name)
            await send_DNDObject_lookup_result(itr, "creatures", found, name)

        @creature.autocomplete("name")
        async def creature_autocomplete(
            itr: discord.Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            return self.data.creatures.get_autocomplete_suggestions(query=current)

        @self.tree.command(
            name=t("commands.class.name"),
            description=t("commands.class.desc"),
        )
        async def character_class(itr: Interaction, name: str):
            log_cmd(itr)
            found = self.data.classes.get(name)
            await send_DNDObject_lookup_result(itr, "classes", found, name)

        @character_class.autocomplete("name")
        async def character_class_autocomplete(
            itr: discord.Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            return self.data.classes.get_autocomplete_suggestions(query=current)

        @self.tree.command(
            name=t("commands.rule.name"), description=t("commands.rule.desc")
        )
        async def rule(itr: Interaction, name: str):
            log_cmd(itr)
            found = self.data.rules.get(name)
            await send_DNDObject_lookup_result(itr, "rules", found, name)

        @rule.autocomplete("name")
        async def rule_autocomplete(
            itr: discord.Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            return self.data.rules.get_autocomplete_suggestions(query=current)

        @self.tree.command(
            name=t("commands.action.name"), description=t("commands.action.desc")
        )
        async def action(itr: Interaction, name: str):
            log_cmd(itr)
            found = self.data.actions.get(name)
            await send_DNDObject_lookup_result(itr, "actions", found, name)

        @action.autocomplete("name")
        async def action_autocomplete(
            itr: discord.Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            return self.data.actions.get_autocomplete_suggestions(query=current)

        @self.tree.command(
            name=t("commands.feat.name"),
            description=t("commands.feat.desc"),
        )
        async def feat(itr: Interaction, name: str):
            log_cmd(itr)
            found = self.data.feats.get(name)
            await send_DNDObject_lookup_result(itr, "feats", found, name)

        @feat.autocomplete("name")
        async def feat_autocomplete(
            itr: discord.Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            return self.data.feats.get_autocomplete_suggestions(query=current)

        @self.tree.command(
            name=t("commands.language.name"),
            description=t("commands.language.desc"),
        )
        async def language(itr: Interaction, name: str):
            log_cmd(itr)
            found = self.data.languages.get(name)
            await send_DNDObject_lookup_result(itr, "languages", found, name)

        @language.autocomplete("name")
        async def language_autocomplete(
            itr: discord.Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            return self.data.languages.get_autocomplete_suggestions(query=current)

        @self.tree.command(
            name=t("commands.background.name"),
            description=t("commands.background.desc"),
        )
        async def background(itr: Interaction, name: str):
            log_cmd(itr)
            found = self.data.backgrounds.get(name)
            await send_DNDObject_lookup_result(itr, "background", found, name)

        @background.autocomplete("name")
        async def background_autocomplete(
            itr: discord.Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            return self.data.backgrounds.get_autocomplete_suggestions(query=current)

        @self.tree.command(
            name=t("commands.search.name"), description=t("commands.search.desc")
        )
        async def search(itr: Interaction, query: str):
            log_cmd(itr)
            results = search_from_query(query, self.data)
            logging.debug(f"Found {len(results.get_all())} results for '{query}'")

            if len(results.get_all()) == 0:
                embed = NoResultsFoundEmbed("results", query)
                await itr.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = SearchEmbed(query, results)
                await itr.response.send_message(
                    embed=embed, view=embed.view, ephemeral=True
                )

        @self.tree.command(
            name=t("commands.namegen.name"), description=t("commands.namegen.desc")
        )
        @app_commands.describe(
            race=t("commands.namegen.args.race"),
            gender=t("commands.namegen.args.gender"),
        )
        @app_commands.choices(gender=GenderChoices)
        async def namegen(
            itr: Interaction, race: str = None, gender: str = Gender.OTHER.value
        ):
            gender = Gender(gender)
            name, new_race, new_gender = self.data.names.get_random(race, gender)

            if name is None:
                await itr.response.send_message(
                    "❌ Can't generate names at this time ❌", ephemeral=True
                )
                return

            description = f"*{new_gender.value} {new_race}*".title()

            embed = SimpleEmbed(title=name, description=description)
            await itr.response.send_message(embed=embed)

        @namegen.autocomplete("race")
        async def autocomplete_namgen_race(
            itr: Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            races = self.data.names.get_races()
            filtered_races = [
                race.title() for race in races if current.lower() in race.lower()
            ]
            return [
                app_commands.Choice(name=race, value=race)
                for race in filtered_races[:25]
            ]

        @self.tree.command(
            name=t("commands.color.name"), description=t("commands.color.desc")
        )
        async def set_color(itr: Interaction, hex_color: str = ""):
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

        @self.tree.command(
            name=t("commands.stats.name"),
            description=t("commands.stats.desc"),
        )
        async def stats(itr: Interaction):
            log_cmd(itr)
            stats = Stats(itr)
            embed = UserActionEmbed(
                itr=itr,
                title=stats.get_embed_title(),
                description=stats.get_embed_description(),
            )
            chart_image = stats.get_radar_chart(itr)
            embed.set_image(url=f"attachment://{chart_image.filename}")
            await itr.response.send_message(embed=embed, file=chart_image)

        @self.tree.command(
            name=t("commands.tokengen.name"),
            description=t("commands.tokengen.desc"),
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
        async def generate_token(
            itr: Interaction,
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

        @self.tree.command(
            name=t("commands.tokengenurl.name"),
            description=t("commands.tokengenurl.desc"),
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
        async def generate_token_from_url(
            itr: Interaction,
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

        @self.tree.command(
            name=t("commands.initiative.name"),
            description=t("commands.initiative.desc"),
        )
        async def initiative(
            itr: Interaction,
        ):
            log_cmd(itr)
            embed = InitiativeEmbed(itr, self.initiatives)
            await itr.response.send_message(embed=embed, view=embed.view)
            await VC.play(itr, SoundType.INITIATIVE)

            message = await itr.original_response()
            await self.initiatives.set_message(itr, message)

        @self.tree.command(
            name=t("commands.plansession.name"),
            description=t("commands.plansession.desc"),
        )
        @app_commands.describe(
            in_weeks=t("commands.plansession.args.in_weeks"),
            poll_duration=t("commands.plansession.args.poll_duration"),
        )
        async def plan_session(
            itr: Interaction,
            in_weeks: app_commands.Range[int, 0, 48],
            poll_duration: app_commands.Range[int, 1, 168] = 24,
        ):
            poll = SessionPlanPoll(in_weeks, poll_duration)
            await itr.response.send_message(poll=poll)

        @self.tree.command(
            name=t("commands.help.name"), description=t("commands.help.desc")
        )
        @app_commands.choices(tab=HelpEmbed.get_tab_choices())
        async def help(itr: Interaction, tab: str = None):
            log_cmd(itr)
            embed = HelpEmbed(tab)
            await itr.response.send_message(
                embed=embed, view=embed.view, ephemeral=True
            )
