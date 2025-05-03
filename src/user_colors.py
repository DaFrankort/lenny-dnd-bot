import discord
import json
import re


class UserColor:
    """Class to handle user colors, which are used in embeds."""
    FILE_PATH = "temp/user_colors.json"

    @staticmethod
    def validate(hex_color: str) -> bool:
        """Validates if the given hex color is in the correct format."""
        hex_color = hex_color.strip("#")
        pattern = re.compile(r"^[0-9a-fA-F]{6}$")
        return pattern.match(hex_color)

    @staticmethod
    def save(interaction: discord.Interaction, color: int) -> None:
        """Saves the user's color to a JSON file."""
        try:
            with open(UserColor.FILE_PATH, "r") as file:
                data = json.load(file)
        except:
            data = {}

        data[str(interaction.user.id)] = color

        with open(UserColor.FILE_PATH, "w") as file:
            json.dump(data, file, indent=4)

    @staticmethod
    def parse(hex_color: str) -> int:
        """Parses a hex color string and returns its integer value."""
        if not hex_color.startswith("#"):
            hex_color = f"#{hex_color}"
        return discord.Color.from_str(hex_color).value

    @staticmethod
    def generate(interaction: discord.Interaction) -> int:
        """Generates a hex value from a username.
        Converts the first 6 characters of a user's display name into a hex value for color.
        If the username is shorter than 6 characters, it uses a fallback value to complete the hex.
        This ensures a unique and deterministic color for each user.
        """
        hex_value = ""
        hex_place = 0

        # This cute little function converts characters into unicode
        # I made it so the the alpha_value assignment line wouldn't be so hard to read
        def get_alpha(char):
            return abs(ord(char.lower()) - 96)

        while hex_place < 6:
            try:
                alpha_value = get_alpha(
                    interaction.user.display_name[hex_place]
                ) * get_alpha(interaction.user.display_name[hex_place + 1])
            except:
                # When username is shorter than 6 characters, inserts replacement value.
                alpha_value = 0  # Value can be changed to 255 for light and blue colors, 0 for dark and red colors.

            if alpha_value > 255:
                alpha_value = alpha_value & 255

            if alpha_value < 16:
                hex_value = hex_value + "0" + hex(alpha_value)[2:]
            else:
                hex_value = hex_value + hex(alpha_value)[2:]

            hex_place += 2
        return UserColor.parse(hex_value)

    @staticmethod
    def get(interaction: discord.Interaction) -> int:
        """Retrieves a user's saved color from the file, or generates one if it does not exist."""
        try:
            with open(UserColor.FILE_PATH, "r") as file:
                data = json.load(file)
                color = data.get(str(interaction.user.id))
        except:
            color = UserColor.generate(interaction)

        if color is None:
            color = UserColor.generate(interaction)

        return color

    @staticmethod
    def remove(interaction: discord.Interaction) -> bool:
        """Removes a user's saved color from the file."""
        try:
            with open(UserColor.FILE_PATH, "r") as file:
                data = json.load(file)
                user_id = str(interaction.user.id)
                if not user_id in data:
                    return False
                del data[user_id]
            with open(UserColor.FILE_PATH, "w") as file:
                json.dump(data, file, indent=4)
            return True
        except Exception as e:
            return False


class ColorEmbed(discord.Embed):
    """Embed class for displaying user color changes."""
    def __init__(self, itr: discord.Interaction, hex_color: str) -> None:
        color = UserColor.parse(hex_color)
        super().__init__(type="rich", color=color)
        self.set_author(
            name=f"{itr.user.display_name} set their color to #{hex_color.upper()}",
            icon_url=itr.user.avatar.url,
        )
