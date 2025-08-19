import discord

from dnd import DNDData, Gender
from embeds import SimpleEmbed

GenderChoices = [
    discord.app_commands.Choice(name="Female", value=Gender.FEMALE.value),
    discord.app_commands.Choice(name="Male", value=Gender.MALE.value),
    discord.app_commands.Choice(name="Other", value=Gender.OTHER.value),
]


class NameGenCommand(discord.app_commands.Command):
    name = "namegen"
    desc = "Generate a random name depending on race and gender!"
    help = "Get a random name for a humanoid, race and gender can be specified but will default to random values."
    command = "/namegen [race] [gender]"

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__(
            name=self.name,
            description=self.desc,
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
        race="Request a name from a specific race, selects random race by default.",
        gender="Request name from a specific gender, selects random gender by default.",
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
