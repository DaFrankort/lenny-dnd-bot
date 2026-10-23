import discord

from embeds.embed import BaseEmbed
from logic.session.stats import UserSessionResult


class UserSessionStatEmbed(BaseEmbed):
    d20_graph: discord.File

    @staticmethod
    def _format_line(number: int, text: str) -> str:
        return f"``{number:>3}`` {text}"

    def __init__(self, result: UserSessionResult):
        super().__init__(title=result.title, description=result.title_description or None, color=result.color)

        self.set_author(name=result.user.display_name, icon_url=result.user.display_avatar.url)

        dice = result.dice
        favorite_die, favorite_uses = dice.most_used_die_type
        self.add_field(
            name="General",
            value="\n".join(
                [
                    self._format_line(dice.total_dice_rolled, "dice rolled total"),
                    self._format_line(favorite_uses, f"favorite die (**d{favorite_die}**) rolls"),
                    self._format_line(dice.adv_count, "advantage rolls"),
                    self._format_line(dice.dis_count, "disadvantage rolls"),
                ]
            ),
        )
        self.add_field(
            name="Damage results",
            value="\n".join(
                [
                    self._format_line(len(dice.damage_totals), "damage rolls"),
                    self._format_line(dice.average_dmg, "damage average"),
                    self._format_line(sum(dice.damage_totals), "damage total"),
                ]
            ),
        )
        self.add_field(name="", value="")  # Padding

        self.add_field(
            name="Raw d20 results",
            value="\n".join(
                [
                    self._format_line(len(dice.rolled_d20_totals), "d20s rolled"),
                    self._format_line(dice.average_rolled_d20, "d20 average"),
                    self._format_line(dice.nat1_count, "natural 1s"),
                    self._format_line(dice.nat20_count, "natural 20s"),
                    self._format_line(dice.dirty20_count, "dirty 20s"),
                ]
            ),
        )
        self.add_field(
            name="Kept d20s",
            value="\n".join(
                [
                    self._format_line(len(dice.kept_d20_totals), "d20s kept"),
                    self._format_line(dice.average_kept_d20, "kept d20 average"),
                    self._format_line(dice.kept_nat1_count, "natural 1s"),
                    self._format_line(dice.kept_nat20_count, "natural 20s"),
                    self._format_line(dice.kept_dirty20_count, "dirty 20s"),
                ]
            ),
        )
        self.add_field(name="", value="")  # Padding

        if result.graph:
            self.set_image(url=f"attachment://{result.graph.filename}")
        self.set_footer(
            text="*kept d20s are dice that counted towards the final result (e.g. the die kept with advantage)."
        )
