import discord
import pytest
from utils.mocking import MockInteraction

from logic.config import Config


class TestConfig:
    @pytest.fixture
    def itr(self) -> discord.Interaction:
        return MockInteraction()

    def test_gamemaster_has_default_permissions(self, itr: discord.Interaction):
        assert itr.guild is not None
        config = Config.get(itr)
        config.reset()

        roles = itr.guild.roles
        allowed_roles = config.allowed_config_roles

        player_role = [role for role in roles if role.name == "player"][0]
        gamemaster_role = [role for role in roles if role.name == "game master"][0]

        assert gamemaster_role.id in allowed_roles, "Game master should be a default allowed role."
        assert player_role.id not in allowed_roles, "Player should not be a default allowed role."

    def test_disallowing_role_disallows_role(self, itr: discord.Interaction):
        assert itr.guild is not None
        config = Config.get(itr)
        config.reset()

        roles = itr.guild.roles
        allowed_roles = config.allowed_config_roles
        gamemaster_role = [role for role in roles if role.name == "game master"][0]

        assert gamemaster_role.id in allowed_roles, "Game master should be a default allowed role."

        config.disallow_permission(gamemaster_role)
        allowed_roles = config.allowed_config_roles

        assert gamemaster_role.id not in allowed_roles, "Game master should be no longer be an allowed role."

    def test_allowing_role_allows_role(self, itr: discord.Interaction):
        assert itr.guild is not None
        config = Config.get(itr)
        config.reset()

        roles = itr.guild.roles
        allowed_roles = config.allowed_config_roles
        player_role = [role for role in roles if role.name == "player"][0]

        assert player_role.id not in allowed_roles, "Player should not be a default allowed role."

        config.allow_permission(player_role)
        allowed_roles = config.allowed_config_roles

        assert player_role.id in allowed_roles, "Player should now be be an allowed role."
