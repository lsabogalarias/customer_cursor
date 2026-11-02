"""Pure routing rules for the API gateway."""

from collections.abc import Mapping

PUBLIC_PATHS: frozenset[str] = frozenset({"auth/login", "auth/register"})


def normalize_path(path: str) -> str:
    """Drop leading and trailing slashes.

    Args:
        path: Path captured under ``/api``.

    Returns:
        Path without surrounding slashes.
    """
    return path.strip("/")


def is_public(path: str) -> bool:
    """Tell whether a path can be called without a bearer token.

    Args:
        path: Path captured under ``/api``.

    Returns:
        True for registration and login only.
    """
    return normalize_path(path) in PUBLIC_PATHS


def resolve_upstream(path: str, upstreams: Mapping[str, str]) -> str | None:
    """Choose the upstream base URL from the first path segment.

    Args:
        path: Path captured under ``/api``.
        upstreams: Map of first segment to base URL.

    Returns:
        The base URL, or None when the segment is unknown.
    """
    normalized = normalize_path(path)
    if not normalized:
        return None
    segment = normalized.split("/", 1)[0]
    return upstreams.get(segment)
