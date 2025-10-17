import json
import logging
import os
import discord


class Profile:
    name: str
    image_url: str | None

    def __init__(self, name: str, image_url: str | None = None):
        self.name = name
        self.image_url = image_url

    def set_name(self, name: str) -> "Profile":
        self.name = name
        UserProfilesCache.save()
        return self

    def set_image(self, image: str | discord.Attachment) -> "Profile":
        if isinstance(image, discord.Attachment):
            # TODO VALIDATE
            print(image.proxy_url)
            self.image_url = image.proxy_url
        else:
            # TODO VALIDATE
            self.image_url = image
        UserProfilesCache.save()
        return self

    def to_dict(self) -> dict:
        return {"name": self.name, "image_url": self.image_url}

    @staticmethod
    def from_dict(data: dict) -> "Profile":
        return Profile(name=data["name"], image_url=data.get("image_url"))


class ProfileList:
    profiles: list[Profile]
    active_profile_index: int

    def __init__(self):
        self.profiles = []
        self.active_profile_index = 0

    def create(self, name: str) -> Profile:
        if len(self.profiles) >= 6:
            raise ValueError("Sorry, you can only have up to 6 profiles.")
        profile = Profile(name)
        self.profiles.append(profile)
        UserProfilesCache.save()
        return profile

    def remove(self, profile_name: str) -> Profile:
        if not self.profiles:
            raise ValueError("You don't have any profiles to remove.")

        remove_index = -1
        for i, profile in enumerate(self.profiles):
            if profile.name == profile_name:
                remove_index = i
                break

        if remove_index == -1:
            raise ValueError(f"No profile found with the name '{profile_name}'.")

        deleted_profile = self.profiles.pop(remove_index)
        if not self.profiles:
            self.active_profile_index = 0
        else:
            if self.active_profile_index >= remove_index:
                self.active_profile_index = max(0, self.active_profile_index - 1)
            self.active_profile_index = min(self.active_profile_index, len(self.profiles) - 1)

        UserProfilesCache.save()
        return deleted_profile

    def set_active(self, profile_name: str) -> Profile:
        for i, profile in enumerate(self.profiles):
            if profile.name.lower() == profile_name.lower():
                self.active_profile_index = i
                UserProfilesCache.save()
                return profile
        raise ValueError(f"No profile found with the name '{profile_name}'.")

    @property
    def active_profile(self) -> Profile | None:
        if not self.profiles:
            raise ValueError("You don't have any profiles.")
        if self.active_profile_index >= len(self.profiles) or self.active_profile_index < 0:
            self.active_profile_index = 0
        return self.profiles[self.active_profile_index]

    def to_dict(self) -> dict:
        return {
            "profiles": [p.to_dict() for p in self.profiles],
            "active_profile_index": self.active_profile_index,
        }

    @staticmethod
    def from_dict(data: dict) -> "ProfileList":
        up = ProfileList()
        up.profiles = [Profile.from_dict(p) for p in data.get("profiles", [])]
        up.active_profile_index = data.get("active_profile_index", 0)
        return up


class UserProfilesCache:
    FILE_PATH = "./temp/user_profiles.json"
    profiles: dict[int, ProfileList] = {}

    @staticmethod
    def load() -> None:
        """Load cache from JSON file (if it exists)."""
        if not os.path.exists(UserProfilesCache.FILE_PATH):
            return

        with open(UserProfilesCache.FILE_PATH, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                logging.warning(f"Generated user profiles cache file {UserProfilesCache.FILE_PATH}")
                data = {}

        for user_id_str, user_data in data.items():
            UserProfilesCache.profiles[int(user_id_str)] = ProfileList.from_dict(user_data)
        logging.info(f"Loaded {len(UserProfilesCache.profiles)} userprofile-lists from cache.")

    @staticmethod
    def save() -> None:
        """Write the current cache to disk as JSON."""
        os.makedirs(os.path.dirname(UserProfilesCache.FILE_PATH), exist_ok=True)
        data = {str(uid): up.to_dict() for uid, up in UserProfilesCache.profiles.items()}
        with open(UserProfilesCache.FILE_PATH, "w") as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def get(itr: discord.Interaction) -> ProfileList:
        """Retrieve the user's profiles from memory."""
        user_id = itr.user.id
        if user_id not in UserProfilesCache.profiles:
            UserProfilesCache.profiles[user_id] = ProfileList()
            UserProfilesCache.save()

        return UserProfilesCache.profiles[user_id]

    @staticmethod
    async def get_profile_choices(
        cmd: discord.app_commands.Command, interaction: discord.Interaction, current: str
    ) -> list[discord.app_commands.Choice[str]]:
        """Get a list of profile choices for the user, with profiles containing `current` first."""
        profile_list = UserProfilesCache.get(interaction)
        active_profile = profile_list.active_profile if profile_list.profiles else None
        current = (current or "").strip().replace(" ", "").lower()
        profiles = sorted(profile_list.profiles, key=lambda p: (0 if current in (p.name).lower() else 1, (p.name).lower()))

        choices = []
        for p in profiles[:25]:
            if p.name == active_profile.name:
                choice = discord.app_commands.Choice(name=f"{p.name} [Current]", value=p.name)
            else:
                choice = discord.app_commands.Choice(name=p.name, value=p.name)
            choices.append(choice)

        return choices[:25]
