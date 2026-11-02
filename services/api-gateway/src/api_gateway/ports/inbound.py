"""Inbound description of the gateway proxy."""

from typing import Protocol


class ProxyRequestPort(Protocol):
    """Forward an authenticated portal call to one service."""

    def route_name(self, path: str) -> str | None:
        """Return the upstream segment for a path.

        Args:
            path: Path under ``/api``.

        Returns:
            The first segment, or None when the path is empty.
        """
        ...
