"""
Backward compatibility module for tts_platform.

.. deprecated::
    Import from `core.platform` instead. This module will be removed in v2.0.
"""

import warnings

warnings.warn(
    "tts_platform is deprecated. Import from core.platform instead.",
    DeprecationWarning,
    stacklevel=2,
)

from core.platform import (  # noqa: F401
    DisplayServer,
    DesktopEnvironment,
    detect_os,
    detect_display_server,
    detect_desktop_environment,
    get_clipboard_text,
    detect_available_engines,
)

__all__ = [
    "DisplayServer",
    "DesktopEnvironment",
    "detect_os",
    "detect_display_server",
    "detect_desktop_environment",
    "get_clipboard_text",
    "detect_available_engines",
]
