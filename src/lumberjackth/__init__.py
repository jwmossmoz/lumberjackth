"""Lumberjack - A modern CLI and Python client for Mozilla Treeherder."""

from lumberjackth.client import TreeherderClient
from lumberjackth.exceptions import (
    LumberjackError,
    TreeherderAPIError,
    TreeherderAuthError,
    TreeherderNotFoundError,
)

__version__ = "1.0.2"
__all__ = [
    "LumberjackError",
    "TreeherderAPIError",
    "TreeherderAuthError",
    "TreeherderClient",
    "TreeherderNotFoundError",
    "__version__",
]
