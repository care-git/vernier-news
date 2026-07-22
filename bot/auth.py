from __future__ import annotations

from telegram.ext import filters


def build_user_filter(allowed_ids: set[int]) -> filters.BaseFilter:
    """A message filter that only passes updates from allow-listed user IDs."""
    return filters.User(user_id=list(allowed_ids))
