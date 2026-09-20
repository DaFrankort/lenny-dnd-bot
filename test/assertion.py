from collections.abc import Iterable
from typing import Any, cast

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


def assert_layout_view_can_be_rendered(view: discord.ui.LayoutView, context: str = "layout_view"):
    """
    Asserts whether a discord.ui.LayoutView or discord.ui.View adheres to Discord component limits.
    Recursively inspects containers, sections, and nested items to validate character counts and bounds.
    """
    try:
        # Helper function to flatten ALL nested components recursively
        def extract_all_components(items: Iterable[discord.ui.Item[Any]]) -> list[discord.ui.Item[Any]]:
            flat: list[discord.ui.Item[Any]] = []
            for item in items:
                flat.append(item)
                children = cast(Iterable[discord.ui.Item[Any]] | None, getattr(item, "children", None))
                if children:
                    flat.extend(extract_all_components(children))
            return flat

        all_components: list[discord.ui.Item[Any]] = extract_all_components(view.children)
        total_chars = 0

        # Check Total Component Limit across whole view (Discord enforces 25 max top-level/nested items)
        assert len(all_components) <= 25, f"{context} exceeds total limit of 25 components ({len(all_components)} present)"

        # Check Top-Level Action Rows / Layout structure
        rows: dict[int, int] = {}
        for child in view.children:
            row_idx = getattr(child, "row", 0) or 0
            width = (
                5
                if isinstance(
                    child,
                    (
                        discord.ui.Select,
                        discord.ui.ChannelSelect,
                        discord.ui.RoleSelect,
                        discord.ui.UserSelect,
                        discord.ui.MentionableSelect,
                    ),
                )
                else 1
            )
            rows[row_idx] = rows.get(row_idx, 0) + width

        assert len(rows) <= 5, f"{context} exceeds maximum of 5 Action Rows (has {len(rows)})"
        for row_num, width in rows.items():
            assert width <= 5, f"{context} Row {row_num} exceeds max width/capacity of 5 slots (used {width})"

        # Check Individual Component Rules & Recursively Accumulate Text
        for i, child in enumerate(all_components):
            # Container / Section Header Text
            title = getattr(child, "title", None)
            if isinstance(title, str) and title:
                total_chars += len(title)
            label = getattr(child, "label", None)
            if isinstance(label, str) and not isinstance(child, (discord.ui.Button, discord.ui.TextInput)):
                total_chars += len(label)

            # Buttons
            if isinstance(child, discord.ui.Button):
                if child.label:
                    assert len(child.label) <= 80, f"{context} Button [{i}] label exceeds 80 chars ({len(child.label)})"
                    total_chars += len(child.label)
                if child.custom_id:
                    assert (
                        len(child.custom_id) <= 100
                    ), f"{context} Button [{i}] custom_id exceeds 100 chars ({len(child.custom_id)})"
                if child.url:
                    assert len(child.url) <= 2048, f"{context} Button [{i}] URL exceeds 2048 chars ({len(child.url)})"

            # Select Menus (String, Channel, Role, User, Mentionable)
            elif isinstance(child, discord.ui.Select):
                if child.placeholder:
                    assert (
                        len(child.placeholder) <= 150
                    ), f"{context} Select [{i}] placeholder exceeds 150 chars ({len(child.placeholder)})"
                    total_chars += len(child.placeholder)
                if child.custom_id:
                    assert (
                        len(child.custom_id) <= 100
                    ), f"{context} Select [{i}] custom_id exceeds 100 chars ({len(child.custom_id)})"

                if hasattr(child, "options") and child.options:
                    assert len(child.options) <= 25, f"{context} Select [{i}] has more than 25 options ({len(child.options)})"
                    for j, opt in enumerate(child.options):
                        assert (
                            len(opt.label) <= 100
                        ), f"{context} Select [{i}] Option [{j}] label exceeds 100 chars ({len(opt.label)})"
                        total_chars += len(opt.label)

                        assert (
                            len(opt.value) <= 100
                        ), f"{context} Select [{i}] Option [{j}] value exceeds 100 chars ({len(opt.value)})"

                        if opt.description:
                            assert (
                                len(opt.description) <= 100
                            ), f"{context} Select [{i}] Option [{j}] description exceeds 100 chars ({len(opt.description)})"
                            total_chars += len(opt.description)

            # Text Inputs
            elif isinstance(child, discord.ui.TextInput):
                if child.label:
                    assert len(child.label) <= 45, f"{context} TextInput [{i}] label exceeds 45 chars ({len(child.label)})"
                    total_chars += len(child.label)
                if child.placeholder:
                    assert (
                        len(child.placeholder) <= 100
                    ), f"{context} TextInput [{i}] placeholder exceeds 100 chars ({len(child.placeholder)})"
                    total_chars += len(child.placeholder)
                if child.custom_id:
                    assert (
                        len(child.custom_id) <= 100
                    ), f"{context} TextInput [{i}] custom_id exceeds 100 chars ({len(child.custom_id)})"
                if child.value:
                    assert len(child.value) <= 4000, f"{context} TextInput [{i}] value exceeds 4000 chars ({len(child.value)})"
                    total_chars += len(child.value)

            # Generic Text components / Section components inside LayoutView
            elif content := getattr(child, "content", None):
                total_chars += len(str(content))

        total_char_limit = 4000
        assert (
            total_chars <= total_char_limit
        ), f"{context} total displayable text size exceeds maximum size of {total_char_limit} chars ({total_chars})"

    except Exception as e:
        pytest.fail(f"Could not render layout view due to an error: {e}")
