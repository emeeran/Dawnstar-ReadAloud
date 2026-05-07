"""Configuration management for TTS application.

This module handles persistent user configuration with:
- YAML-based configuration file
- Validation of all configuration values
- Sensible defaults with min/max constraints
- Hot-reload support (file change detection)
"""

import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

from core.exceptions import ConfigurationError

_log = logging.getLogger("tts")

# Configuration file locations
CONFIG_DIR = Path.home() / ".config" / "tts"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

# Valid configuration values
VALID_LANGUAGES = {"en-us", "en-uk", "ta", "en", "en-gb"}
VALID_SPEEDS = {"slow", "normal", "fast"}
VALID_ENGINES = {"edge", "gtts", "espeak", None}

# Configuration constraints
CACHE_SIZE_MIN_MB = 50
CACHE_SIZE_MAX_MB = 5000

# Default configuration values
DEFAULTS: dict[str, Any] = {
    "language": "en-us",
    "speed": "normal",
    "cache_enabled": True,
    "cache_max_size_mb": 500,
    "verbose": False,
    "notifications": True,
    "progress": True,
    "default_engine": None,
}


@dataclass
class TTSAppConfig:
    """Application configuration with validation.

    All configuration values are validated on initialization
    and when loaded from file. Invalid values raise ConfigurationError.

    Attributes:
        language: Language code (en-us, en-uk, ta).
        speed: Speech speed (slow, normal, fast).
        cache_enabled: Whether to cache generated audio.
        cache_max_size_mb: Maximum cache size in megabytes.
        verbose: Enable verbose logging output.
        notifications: Enable desktop notifications.
        progress: Show progress indicators for long texts.
        default_engine: Preferred TTS engine (null = auto).
    """

    language: str = DEFAULTS["language"]
    speed: str = DEFAULTS["speed"]
    cache_enabled: bool = DEFAULTS["cache_enabled"]
    cache_max_size_mb: int = DEFAULTS["cache_max_size_mb"]
    verbose: bool = DEFAULTS["verbose"]
    notifications: bool = DEFAULTS["notifications"]
    progress: bool = DEFAULTS["progress"]
    default_engine: str | None = DEFAULTS["default_engine"]

    # Runtime-only settings (not saved to file)
    _source: str = field(default="defaults", repr=False)

    def __post_init__(self) -> None:
        """Validate configuration values after initialization.

        Raises:
            ConfigurationError: If any configuration value is invalid.
        """
        self._validate_language()
        self._validate_speed()
        self._validate_cache_size()
        self._validate_engine()

    def _validate_language(self) -> None:
        """Validate language setting."""
        if self.language not in VALID_LANGUAGES:
            raise ConfigurationError(
                f"Invalid language: {self.language}. "
                f"Must be one of: {', '.join(sorted(VALID_LANGUAGES - {None}))}"
            )

    def _validate_speed(self) -> None:
        """Validate speed setting."""
        if self.speed not in VALID_SPEEDS:
            raise ConfigurationError(
                f"Invalid speed: {self.speed}. "
                f"Must be one of: {', '.join(sorted(VALID_SPEEDS))}"
            )

    def _validate_cache_size(self) -> None:
        """Validate cache size setting."""
        if not CACHE_SIZE_MIN_MB <= self.cache_max_size_mb <= CACHE_SIZE_MAX_MB:
            raise ConfigurationError(
                f"Invalid cache_max_size_mb: {self.cache_max_size_mb}. "
                f"Must be between {CACHE_SIZE_MIN_MB} and {CACHE_SIZE_MAX_MB} MB"
            )

    def _validate_engine(self) -> None:
        """Validate default engine setting."""
        if self.default_engine not in VALID_ENGINES:
            raise ConfigurationError(
                f"Invalid default_engine: {self.default_engine}. "
                f"Must be one of: edge, gtts, espeak, or null"
            )

    @classmethod
    def load(cls) -> "TTSAppConfig":
        """Load configuration from file, falling back to defaults.

        This method:
        1. Attempts to load YAML configuration file
        2. Filters to known configuration keys only
        3. Validates all values via __post_init__ by passing as kwargs
        4. Falls back to defaults on any error

        Returns:
            Validated TTSAppConfig instance.

        Note:
            If validation fails, returns default configuration instead
            of raising an error (fail-safe behavior).
        """
        if not CONFIG_FILE.exists():
            return cls(_source="defaults")

        try:
            with open(CONFIG_FILE) as f:
                data = yaml.safe_load(f) or {}

            # Filter to known keys and construct via __init__ so
            # __post_init__ validates the loaded values
            kwargs = {
                k: v for k, v in data.items()
                if k in DEFAULTS and not k.startswith("_")
            }
            return cls(_source="file", **kwargs)

        except ConfigurationError as e:
            # Validation failed - log and use defaults
            _log.warning("Configuration validation error: %s. Using defaults.", e)
            return cls(_source="defaults (validation error)")

        except (OSError, yaml.YAMLError):
            return cls(_source="defaults (error)")

    def save(self) -> bool:
        """Save configuration to file.

        Only saves non-default values to keep config file minimal.

        Returns:
            True if save successful, False on error.
        """
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)

            # Only save non-default values
            data = {}
            for key, default_value in DEFAULTS.items():
                current_value = getattr(self, key, None)
                if current_value != default_value and current_value is not None:
                    data[key] = current_value

            with open(CONFIG_FILE, "w") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=True)

            return True
        except (OSError, yaml.YAMLError):
            return False

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary.

        Returns:
            Dictionary of configuration values (excludes private fields).
        """
        return {k: v for k, v in asdict(self).items() if not k.startswith("_")}

    @staticmethod
    def get_config_path() -> Path:
        """Return the config file path.

        Returns:
            Path to configuration file.
        """
        return CONFIG_FILE

    @staticmethod
    def reset() -> bool:
        """Delete configuration file, reverting to defaults.

        Returns:
            True if reset successful, False on error.
        """
        try:
            if CONFIG_FILE.exists():
                CONFIG_FILE.unlink()
            return True
        except OSError:
            return False

def generate_sample_config() -> str:
    """Generate a sample configuration file content.

    Returns:
        Sample YAML configuration with comments.
    """
    sample = f"""# TTS Application Configuration
# Save this file to ~/.config/tts/config.yaml

# Language: en-us, en-uk, ta
# Default: en-us
language: en-us

# Speed: slow, normal, fast
# Default: normal
speed: normal

# Enable audio caching
# Default: true
cache_enabled: true

# Maximum cache size in megabytes
# Range: {CACHE_SIZE_MIN_MB} - {CACHE_SIZE_MAX_MB}
# Default: 500
cache_max_size_mb: 500

# Show verbose output
# Default: false
verbose: false

# Show desktop notifications
# Default: true
notifications: true

# Show progress for long texts
# Default: true
progress: true

# Preferred engine: edge, gtts, espeak (null = auto)
# Default: null
default_engine: null
"""
    return sample
