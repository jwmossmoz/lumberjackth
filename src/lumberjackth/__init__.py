"""Lumberjack - A modern CLI and Python client for Mozilla Treeherder."""

from lumberjackth.client import TreeherderClient
from lumberjackth.exceptions import (
    LumberjackError,
    TreeherderAPIError,
    TreeherderAuthError,
    TreeherderNotFoundError,
)

__version__ = "1.3.0"
__all__ = [
    "LumberjackError",
    "TreeherderAPIError",
    "TreeherderAuthError",
    "TreeherderClient",
    "TreeherderNotFoundError",
    "__version__",
]
