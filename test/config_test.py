from logic.config import Config
from utils.mocking import MockGuild


class TestConfig:
    def test_gamemaster_has_default_permissions(self):
        server = MockGuild(1000)
        config = Config(server)
        config.reset()

        roles = server.roles
        allowed_roles = config.get_allowed_config_roles()

        player_role = [role for role in roles if role.name == "player"][0]
        gamemaster_role = [role for role in roles if role.name == "game master"][0]

        assert gamemaster_role.id in allowed_roles, "Game master should be a default allowed role."
        assert player_role.id not in allowed_roles, "Player should not be a default allowed role."

    def test_disallowing_role_disallows_role(self):
        server = MockGuild(1001)
        config = Config(server)
        config.reset()

        roles = server.roles
        allowed_roles = config.get_allowed_config_roles()
        gamemaster_role = [role for role in roles if role.name == "game master"][0]

        assert gamemaster_role.id in allowed_roles, "Game master should be a default allowed role."

        config.disallow_permission(gamemaster_role)
        allowed_roles = config.get_allowed_config_roles()

        assert gamemaster_role.id not in allowed_roles, "Game master should be no longer be an allowed role."

    def test_allowing_role_allows_role(self):
        server = MockGuild(1001)
        config = Config(server)
        config.reset()

        roles = server.roles
        allowed_roles = config.get_allowed_config_roles()
        player_role = [role for role in roles if role.name == "player"][0]

        assert player_role.id not in allowed_roles, "Player should not be a default allowed role."

        config.allow_permission(player_role)
        allowed_roles = config.get_allowed_config_roles()

        assert player_role.id in allowed_roles, "Player should now be be an allowed role."
