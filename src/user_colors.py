import discord
import json
import os
import re

class UserColor:
    FILE_PATH = "temp/user_colors.json"

    def __init__(self, itr: discord.Interaction, hex_value: str):
        self.is_valid = True
        hex_value = hex_value.lower()
        if hex_value.startswith("#"):
            hex_value = hex_value[1:]
        
        HEX_PATTERN = re.compile(r"^[0-9a-fA-F]{6}$")
        if not HEX_PATTERN.match(hex_value):
            self.is_valid = False
            print(f"  !!! Invalid hex value \"{hex_value}\": Must be 6 valid hexadecimal characters (0-9, A-F) !!!")
            return
        
        self.hex_value = hex_value
        self.user_id = itr.user.id
    
    def save(self):
        """Saves the user's color to a JSON file."""
        data = {}
        if os.path.exists(self.FILE_PATH):
            with open(self.FILE_PATH, "r") as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    data = {}

        data[str(self.user_id)] = self.hex_value

        with open(self.FILE_PATH, "w") as file:
            json.dump(data, file, indent=4)

    @classmethod
    def load(cls, user_id: str):
        """Retrieves a user's saved color from the file."""
        user_id = str(user_id)

        # Load data if the file exists
        if os.path.exists(cls.FILE_PATH):
            with open(cls.FILE_PATH, "r") as file:
                try:
                    data = json.load(file)
                    return data.get(user_id, None)  # Return the color or None
                except json.JSONDecodeError:
                    return None

        return None
    
    @classmethod
    def remove(cls, user_id: str) -> bool:
        """Removes a user's saved color from the file."""
        user_id = str(user_id)

        if not os.path.exists(cls.FILE_PATH):
            return False
        
        with open(cls.FILE_PATH, 'r') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                return False
            
        if not user_id in data:
            return False
        
        del data[user_id]
        with open(cls.FILE_PATH, "w") as file:
            json.dump(data, file, indent=4)
        return True
    
    def get(self) -> discord.Color:
        return discord.Color.from_str(f"#{self.hex_value}")

class ColorEmbed:
    def __init__(self, itr: discord.Interaction, user_color: UserColor):
        self.user_color = user_color
        self.avatar_url = itr.user.avatar.url
        self.username = itr.user.display_name
    
    def build(self):
        embed = discord.Embed(type="rich")
        embed.set_author(
            name=f"{self.username} set their color to #{self.user_color.hex_value.upper()}",
            icon_url=self.avatar_url
        )
        embed.color = self.user_color.get()
        return embed