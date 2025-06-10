import logging
import os
import discord
from discord import app_commands
from discord import Interaction
from dotenv import load_dotenv

from dice import DiceExpression, DiceRollMode
from dnd import DNDData, DNDObject
from embeds import (
    NoResultsFoundEmbed,
    MultiDNDSelectView,
    SimpleEmbed,
    SuccessEmbed,
    UserActionEmbed,
)
from initiative import (
    Initiative,
    InitiativeTracker,
    InitiativeTrackerEmbed,
)
from search import SearchEmbed, search_from_query
from stats import Stats
from token_gen import (
    AlignH,
    AlignV,
    generate_token_filename,
    generate_token_image,
    generate_token_url_filename,
    image_to_bytesio,
    open_image,
    open_image_url,
)
from user_colors import UserColor
from voice_chat import VC, SoundType, Sounds


class Bot(discord.Client):
    tree: app_commands.CommandTree
    token: str
    guild_id: int
    data: DNDData
    initiatives: InitiativeTracker

    def __init__(self):
        load_dotenv()
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)
        self.token = os.getenv("DISCORD_BOT_TOKEN")
        self.guild_id = int(os.getenv("GUILD_ID"))

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
        VC.check_ffmpeg()
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
                if embed.view is None:
                    await itr.response.send_message(embed=embed)
                    return
                await itr.response.send_message(embed=embed, view=view)

        #
        # COMMANDS
        #

        @self.tree.command(name="roll", description="Roll your d20s!")
        async def roll(itr: Interaction, diceroll: str, reason: str = None):
            log_cmd(itr)
            expression = DiceExpression(
                diceroll, mode=DiceRollMode.Normal, reason=reason
            )
            await itr.response.send_message(
                embed=UserActionEmbed(
                    itr=itr,
                    title=expression.title,
                    description=expression.description,
                ),
                ephemeral=expression.ephemeral,
            )
            await VC.play_dice_roll(itr, expression, reason)

        @self.tree.command(name="d20", description="Just roll a clean d20")
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
            name="advantage", description="Lucky you! Roll and take the best of two!"
        )
        async def advantage(itr: Interaction, diceroll: str, reason: str = None):
            log_cmd(itr)
            expression = DiceExpression(diceroll, DiceRollMode.Advantage, reason=reason)
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
            name="disadvantage",
            description="Tough luck chump... Roll twice and suck it.",
        )
        async def disadvantage(itr: Interaction, diceroll: str, reason: str = None):
            log_cmd(itr)
            expression = DiceExpression(
                diceroll, DiceRollMode.Disadvantage, reason=reason
            )
            await itr.response.send_message(
                embed=UserActionEmbed(
                    itr=itr,
                    title=expression.title,
                    description=expression.description,
                ),
                ephemeral=expression.ephemeral,
            )
            await VC.play_dice_roll(itr, expression, reason)

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

        @self.tree.command(name="spell", description="Get the details for a spell.")
        async def spell(itr: Interaction, name: str):
            log_cmd(itr)
            found = self.data.spells.get(name)
            await send_DNDObject_lookup_result(itr, "spells", found, name)

        @spell.autocomplete("name")
        async def spell_autocomplete(
            itr: discord.Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            return self.data.spells.get_autocomplete_suggestions(query=current)

        @self.tree.command(name="item", description="Get the details for an item.")
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
            name="condition", description="Get the details for a condition."
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
            name="creature", description="Get the details for a creature."
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
            name="class", description="Get the details for a character-class."
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

        @self.tree.command(name="rule", description="Look up D&D rules.")
        async def rule(itr: Interaction, name: str):
            log_cmd(itr)
            found = self.data.rules.get(name)
            await send_DNDObject_lookup_result(itr, "rules", found, name)

        @rule.autocomplete("name")
        async def rule_autocomplete(
            itr: discord.Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            return self.data.rules.get_autocomplete_suggestions(query=current)

        @self.tree.command(name="action", description="Get the details for an action.")
        async def action(itr: Interaction, name: str):
            log_cmd(itr)
            found = self.data.actions.get(name)
            await send_DNDObject_lookup_result(itr, "actions", found, name)

        @action.autocomplete("name")
        async def action_autocomplete(
            itr: discord.Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            return self.data.actions.get_autocomplete_suggestions(query=current)

        @self.tree.command(name="search", description="Search for a spell.")
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
            name="color",
            description="Set a preferred color using a hex-value. Leave hex_color empty to use auto-generated colors.",
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
            name="stats",
            description="Roll stats for a new character, using the 4d6 drop lowest method.",
        )
        async def stats(itr: Interaction):
            log_cmd(itr)
            stats = Stats(itr)
            await itr.response.send_message(
                embed=UserActionEmbed(
                    itr=itr,
                    title=stats.get_embed_title(),
                    description=stats.get_embed_description(),
                ),
            )

        @self.tree.command(
            name="tokengen", description="Turn an image into a 5etools-style token."
        )
        @app_commands.describe(
            image="The image to turn into a token.",
            frame_hue="Hue shift to apply to the token-frame (Gold: 0 | Red: -30 | Blue: 180 | Green: 80).",
            h_alignment="Horizontal alignment for the token image.",
            v_alignment="Vertical alignment for the token image.",
        )
        @app_commands.choices(
            h_alignment=[
                app_commands.Choice(name="Left", value=AlignH.LEFT.value),
                app_commands.Choice(name="Center", value=AlignH.CENTER.value),
                app_commands.Choice(name="Right", value=AlignH.RIGHT.value),
            ],
            v_alignment=[
                app_commands.Choice(name="Top", value=AlignV.TOP.value),
                app_commands.Choice(name="Center", value=AlignV.CENTER.value),
                app_commands.Choice(name="Bottom", value=AlignV.BOTTOM.value),
            ],
        )
        async def generate_token(
            itr: Interaction,
            image: discord.Attachment,
            frame_hue: app_commands.Range[int, -360, 360] = 0,
            h_alignment: str = AlignH.CENTER.value,
            v_alignment: str = AlignV.CENTER.value,
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
            await itr.followup.send(
                file=discord.File(
                    fp=image_to_bytesio(token_image),
                    filename=generate_token_filename(image),
                )
            )

        @self.tree.command(
            name="tokengenurl",
            description="Turn an image-url into a 5etools-style token.",
        )
        @app_commands.describe(
            url="The image-url to generate a token from.",
            frame_hue="Hue shift to apply to the token-frame (Gold: 0 | Red: -30 | Blue: 180 | Green: 80).",
            h_alignment="Horizontal alignment for the token image.",
            v_alignment="Vertical alignment for the token image.",
        )
        @app_commands.choices(
            h_alignment=[
                app_commands.Choice(name="Left", value=AlignH.LEFT.value),
                app_commands.Choice(name="Center", value=AlignH.CENTER.value),
                app_commands.Choice(name="Right", value=AlignH.RIGHT.value),
            ],
            v_alignment=[
                app_commands.Choice(name="Top", value=AlignV.TOP.value),
                app_commands.Choice(name="Center", value=AlignV.CENTER.value),
                app_commands.Choice(name="Bottom", value=AlignV.BOTTOM.value),
            ],
        )
        async def generate_token_from_url(
            itr: Interaction,
            url: str,
            frame_hue: app_commands.Range[int, -360, 360] = 0,
            h_alignment: str = AlignH.CENTER.value,
            v_alignment: str = AlignV.CENTER.value,
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
            await itr.followup.send(
                file=discord.File(
                    fp=image_to_bytesio(token_image),
                    filename=generate_token_url_filename(url),
                )
            )

        @self.tree.command(
            name="initiative", description="Roll initiative for yourself or a creature."
        )
        @app_commands.describe(
            modifier="The initiative modifier to apply to the roll.",
            name="The unique name of the creature you're rolling initiative for (leave blank to roll for yourself).",
        )
        async def initiative(itr: Interaction, modifier: int, name: str | None = None):
            log_cmd(itr)
            initiative = Initiative(itr, modifier, name)
            self.initiatives.add(itr, initiative)
            await itr.response.send_message(
                embed=UserActionEmbed(
                    itr=itr, title=initiative.title, description=initiative.description
                )
            )
            await VC.play_initiative_roll(itr, initiative)

        @self.tree.command(
            name="setinitiative",
            description="Set initiative for yourself or a creature.",
        )
        @app_commands.describe(
            value="The initiative value to use.",
            name="The unique name of the creature you're rolling initiative for (leave blank to roll for yourself).",
        )
        async def set_initiative(itr: Interaction, value: int, name: str | None = None):
            log_cmd(itr)
            initiative = Initiative(itr, 0, name)
            initiative.set_value(value)
            self.initiatives.add(itr, initiative)
            await itr.response.send_message(
                embed=UserActionEmbed(
                    itr=itr, title=initiative.title, description=initiative.description
                )
            )

        @set_initiative.autocomplete("name")
        async def set_initiative_autocomplete(
            itr: discord.Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            return self.initiatives.get_autocomplete_suggestions(itr, current)

        @self.tree.command(
            name="bulkinitiative",
            description="Roll initiative for a defined amount of creatures.",
        )
        @app_commands.describe(
            modifier="The initiative modifier to apply to the roll.",
            name="The names to use for the creatures.",
            amount="The amount of creatures to create.",
            shared="Use the same initiative value for all creatures?",
        )
        async def bulk_initiative(
            itr: Interaction,
            modifier: int,
            name: str,
            amount: app_commands.Range[int, 1],
            shared: bool = False,
        ):
            log_cmd(itr)
            title, description = self.initiatives.add_bulk(
                itr=itr, modifier=modifier, name=name, amount=amount, shared=shared
            )
            await itr.response.send_message(
                embed=UserActionEmbed(itr=itr, title=title, description=description)
            )
            await VC.play(itr, SoundType.ROLL)

        @self.tree.command(
            name="showinitiative",
            description="Show an overview of all the rolled initiatives.",
        )
        async def show_initiative(itr: Interaction):
            log_cmd(itr)

            if self.initiatives.get(itr) == []:
                await itr.response.send_message(
                    f"❌ There are no initiatives for {itr.guild.name} ❌",
                    ephemeral=True,
                )
                return

            embed = InitiativeTrackerEmbed(itr, self.initiatives)
            await itr.response.send_message(embed=embed)

        @self.tree.command(
            name="clearinitiative", description="Clear all initiative rolls."
        )
        async def clear_initiative(itr: Interaction):
            log_cmd(itr)
            self.initiatives.clear(itr)
            await itr.response.send_message(
                embed=SimpleEmbed(
                    "Cleared all initiatives!", f"Cleared by {itr.user.display_name}."
                )
            )

        @self.tree.command(
            name="removeinitiative",
            description="Remove a single initiative roll from the list.",
        )
        async def remove_initiative(itr: Interaction, target: str | None = None):
            log_cmd(itr)
            text, success = self.initiatives.remove(itr, target)
            await itr.response.send_message(
                embed=SuccessEmbed(
                    title_success="Removed initiative",
                    title_fail="Failed to remove initiative",
                    description=text,
                    success=success,
                ),
                ephemeral=not success,
            )

        @remove_initiative.autocomplete("target")
        async def remove_initiative_autocomplete(
            itr: discord.Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            return self.initiatives.get_autocomplete_suggestions(itr, current)

        @self.tree.command(
            name="swapinitiative",
            description="Swap the initiative order of two creatures or players (useful for feats like Alert).",
        )
        async def swap_initiative(itr: Interaction, target_a: str, target_b: str):
            log_cmd(itr)
            text, success = self.initiatives.swap(itr, target_a, target_b)
            await itr.response.send_message(
                embed=SuccessEmbed(
                    title_success="Swapped initiative",
                    title_fail="Failed to swap initiative",
                    description=text,
                    success=success,
                ),
                ephemeral=not success,
            )

        @swap_initiative.autocomplete("target_a")
        async def swap_target_a_autocomplete(
            itr: discord.Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            return self.initiatives.get_autocomplete_suggestions(itr, current)

        @swap_initiative.autocomplete("target_b")
        async def swap_target_b_autocomplete(
            itr: discord.Interaction, current: str
        ) -> list[app_commands.Choice[str]]:
            return self.initiatives.get_autocomplete_suggestions(itr, current)
