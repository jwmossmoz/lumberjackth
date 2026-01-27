"""Lumberjack - A modern CLI and Python client for Mozilla Treeherder."""

from lumberjack.client import TreeherderClient
from lumberjack.exceptions import (
    LumberjackError,
    TreeherderAPIError,
    TreeherderAuthError,
    TreeherderNotFoundError,
)

__version__ = "0.1.0"
__all__ = [
    "LumberjackError",
    "TreeherderAPIError",
    "TreeherderAuthError",
    "TreeherderClient",
    "TreeherderNotFoundError",
    "__version__",
]
