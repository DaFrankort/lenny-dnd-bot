import discord
import pytest
from utils.mocking import MockInteraction

from logic.config import (
    DEFAULT_DISALLOWED_OFFICIAL_SOURCES,
    OFFICIAL_SOURCES,
    PARTNERED_SOURCES,
    Config,
)


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

    def test_official_sources_are_enabled_by_default(self, itr: discord.Interaction):
        # All official sources, minus the default disallowed ones, of course
        assert itr.guild is not None
        config = Config.get(itr)
        config.reset()

        sources = OFFICIAL_SOURCES
        disallowed_sources = DEFAULT_DISALLOWED_OFFICIAL_SOURCES

        for source in sources.source_ids:
            if source in disallowed_sources:
                assert not config.config.is_source_allowed(source)
            else:
                assert config.config.is_source_allowed(source)

    def test_partnered_sources_are_disabled_by_default(self, itr: discord.Interaction):
        assert itr.guild is not None
        config = Config.get(itr)
        config.reset()

        sources = PARTNERED_SOURCES

        for source in sources.source_ids:
            assert not config.config.is_source_allowed(source)

    def test_changing_an_official_source_does_not_change_partnered_sources(self, itr: discord.Interaction):
        assert itr.guild is not None
        config = Config.get(itr)
        config.reset()

        sources = OFFICIAL_SOURCES.source_ids
        for source in sources:
            allowed_partnered_sources_1 = sorted(config.config.allowed_partnered_sources)
            disallowed_partnered_sources_1 = sorted(config.config.disallowed_partnered_sources)

            config.disallow_source(source)

            allowed_partnered_sources_2 = sorted(config.config.allowed_partnered_sources)
            disallowed_partnered_sources_2 = sorted(config.config.disallowed_partnered_sources)

            config.allow_source(source)

            allowed_partnered_sources_3 = sorted(config.config.allowed_partnered_sources)
            disallowed_partnered_sources_3 = sorted(config.config.disallowed_partnered_sources)

            # https://docs.pytest.org/en/latest/how-to/assert.html#making-use-of-context-sensitive-comparisons
            # Pytest should be smart enough to handle list assertions
            assert allowed_partnered_sources_1 == allowed_partnered_sources_2
            assert allowed_partnered_sources_1 == allowed_partnered_sources_3
            assert allowed_partnered_sources_2 == allowed_partnered_sources_3

            assert disallowed_partnered_sources_1 == disallowed_partnered_sources_2
            assert disallowed_partnered_sources_1 == disallowed_partnered_sources_3
            assert disallowed_partnered_sources_2 == disallowed_partnered_sources_3

    def test_changing_a_partnered_source_does_not_change_official_sources(self, itr: discord.Interaction):
        assert itr.guild is not None
        config = Config.get(itr)
        config.reset()

        sources = PARTNERED_SOURCES.source_ids
        for source in sources:
            allowed_official_sources_1 = sorted(config.config.allowed_official_sources)
            disallowed_official_sources_1 = sorted(config.config.disallowed_official_sources)

            config.disallow_source(source)

            allowed_official_sources_2 = sorted(config.config.allowed_official_sources)
            disallowed_official_sources_2 = sorted(config.config.disallowed_official_sources)

            config.allow_source(source)

            allowed_official_sources_3 = sorted(config.config.allowed_official_sources)
            disallowed_official_sources_3 = sorted(config.config.disallowed_official_sources)

            # idem test_changing_an_official_source_does_not_change_partnered_sources
            assert allowed_official_sources_1 == allowed_official_sources_2
            assert allowed_official_sources_1 == allowed_official_sources_3
            assert allowed_official_sources_2 == allowed_official_sources_3

            assert disallowed_official_sources_1 == disallowed_official_sources_2
            assert disallowed_official_sources_1 == disallowed_official_sources_3
            assert disallowed_official_sources_2 == disallowed_official_sources_3
