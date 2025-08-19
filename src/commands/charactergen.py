import discord

from dnd import DNDData, Gender
from embeds import SimpleEmbed
from i18n import t

GenderChoices = [
    discord.app_commands.Choice(name="Female", value=Gender.FEMALE.value),
    discord.app_commands.Choice(name="Male", value=Gender.MALE.value),
    discord.app_commands.Choice(name="Other", value=Gender.OTHER.value),
]


class NameGenCommand(discord.app_commands.Command):
    name = t("commands.namegen.name")
    description = t("commands.namegen.desc")

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__(
            name=self.name,
            description=self.description,
            callback=self.callback,
        )

    async def race_autocomplete(self, _: discord.Interaction, current: str):
        races = self.data.names.get_races()
        filtered_races = [
            race.title() for race in races if current.lower() in race.lower()
        ]
        return [
            discord.app_commands.Choice(name=race, value=race)
            for race in filtered_races[:25]
        ]

    @discord.app_commands.describe(
        race=t("commands.namegen.args.race"),
        gender=t("commands.namegen.args.gender"),
    )
    @discord.app_commands.choices(gender=GenderChoices)
    @discord.app_commands.autocomplete(race=race_autocomplete)
    async def callback(
        self,
        itr: discord.Interaction,
        race: str = None,
        gender: str = Gender.OTHER.value,
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
