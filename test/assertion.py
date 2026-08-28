import discord
import pytest


def assert_embed_can_be_rendered(embed: discord.Embed, context: str = "embed"):
    """
    Asserts if an embed does not exceed its character limits.
    This will throw errors which come from the external discord API, and thus can't be tested directly.
    """

    try:
        embed_dict = embed.to_dict()
        total_chars = 0

        # Check Title (256 max)
        if title := embed_dict.get("title"):
            assert len(title) <= 256, f"{context} Title exceeds 256 chars ({len(title)})"
            total_chars += len(title)

        # Check Description (4096 max)
        if desc := embed_dict.get("description"):
            assert len(desc) <= 4096, f"{context} description exceeds 4096 chars ({len(desc)})"
            total_chars += len(desc)

        # Check Footer (2048 max)
        if footer := embed_dict.get("footer", {}).get("text"):
            assert len(footer) <= 2048, f"{context} footer exceeds 2048 chars ({len(footer)})"
            total_chars += len(footer)

        # Check Author (256 max)
        if author := embed_dict.get("author", {}).get("name"):
            assert len(author) <= 256, f"{context} author exceeds 256 chars ({len(author)})"
            total_chars += len(author)

        # Check Fields (Name: 256 max, Value: 1024 max)
        fields = embed_dict.get("fields", [])
        assert len(fields) <= 25, f"{context} has more than 25 fields ({len(fields)})"

        for i, field in enumerate(fields):
            name = field.get("name", "")
            value = field.get("value", "")

            assert len(name) <= 256, f"{context} field {i} name exceeds 256 chars ({len(name)})"
            assert len(value) <= 1024, f"{context} field {i} value exceeds 1024 chars ({len(value)})"

            total_chars += len(name) + len(value)

        total_char_limit = 6000
        assert total_chars <= total_char_limit, f"{context} total embed size exceeds {total_char_limit} chars ({total_chars})"

    except Exception as e:
        pytest.fail(f"Could not render embed due to an error: {e}")
