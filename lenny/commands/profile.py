import discord

from commands.command import SimpleCommand, SimpleCommandGroup
from embeds.embed import SimpleEmbed
from embeds.profile import ProfileEmbed
from logic.profile import ProfileData


class ProfileCommandGroup(SimpleCommandGroup):
    name = "profile"
    desc = "Manage your character profiles!"

    def __init__(self):
        super().__init__()
        self.add_command(ProfileSelectCommand())
        self.add_command(ProfileCreateCommand())
        self.add_command(ProfileRemoveCommand())
        self.add_command(ProfileEditCommandGroup())


class ProfileCreateCommand(SimpleCommand):
    name = "create"
    desc = "Create a new character profile!"
    help = "Creates a new character profile with the given name."

    async def handle(self, itr: discord.Interaction, name: str):
        self.log(itr)
        result = ProfileData.get(itr).add(name)
        embed = ProfileEmbed(itr, result)
        await itr.response.send_message(embed=embed, ephemeral=True)


class ProfileSelectCommand(SimpleCommand):
    name = "select"
    desc = "Activate an existing character profile!"
    help = "Selects an existing character profile to be the active profile."

    # @discord.app_commands.autocomplete(profile=UserProfilesCache.get_profile_choices)
    async def handle(self, itr: discord.Interaction, profile: str):
        self.log(itr)
        await itr.response.send_message("UNDER CONSTRUCTION")
        # result = UserProfilesCache.get(itr).set_active(profile)
        # embed = ProfileEmbed(itr, result)
        # await itr.response.send_message(embed=embed, ephemeral=True)


class ProfileRemoveCommand(SimpleCommand):
    name = "remove"
    desc = "Remove an existing character profile!"
    help = "Removes the character profile at the given index."

    # @discord.app_commands.autocomplete(profile=UserProfilesCache.get_profile_choices)
    async def handle(self, itr: discord.Interaction, profile: str):
        self.log(itr)
        result = ProfileData.get(itr).delete(profile)
        embed = SimpleEmbed(title="Profile Removed", description=f"Removed profile '{result.name}'.", color=discord.Color.red())
        await itr.response.send_message(embed=embed, ephemeral=True)


class ProfileEditCommandGroup(SimpleCommandGroup):
    name = "edit"
    desc = "Edit various aspects of your character profile!"

    def __init__(self):
        super().__init__()
        self.add_command(ProfileEditNameCommand())
        self.add_command(ProfileEditImageCommand())


class ProfileEditNameCommand(SimpleCommand):
    name = "name"
    desc = "Edit your character's name!"
    help = "Edits the name to use for your character."

    async def handle(self, itr: discord.Interaction, name: str):
        self.log(itr)
        await itr.response.send_message("UNDER CONSTRUCTION")
        # result = UserProfilesCache.get(itr).active_profile.set_name(name)
        # embed = ProfileEmbed(itr, result)
        # await itr.response.send_message(embed=embed, ephemeral=True)


class ProfileEditImageCommand(SimpleCommand):
    name = "image"
    desc = "Edit your profile's image!"
    help = "Changes the image to use for your character via an uploaded image file."

    def __init__(self):
        super().__init__()

    async def handle(self, itr: discord.Interaction, image: discord.Attachment):
        self.log(itr)
        await itr.response.send_message("UNDER CONSTRUCTION")
        # result = UserProfilesCache.get(itr).active_profile.set_image(image)
        # embed = ProfileEmbed(itr, result)
        # await itr.response.send_message(embed=embed, ephemeral=True)
