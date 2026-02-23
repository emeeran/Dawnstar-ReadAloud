"""Configuration management for TTS application."""

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


# Configuration file locations
CONFIG_DIR = Path.home() / ".config" / "tts"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

# Default configuration values
DEFAULTS = {
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
    """Application configuration with defaults."""

    language: str = DEFAULTS["language"]
    speed: str = DEFAULTS["speed"]
    cache_enabled: bool = DEFAULTS["cache_enabled"]
    cache_max_size_mb: int = DEFAULTS["cache_max_size_mb"]
    verbose: bool = DEFAULTS["verbose"]
    notifications: bool = DEFAULTS["notifications"]
    progress: bool = DEFAULTS["progress"]
    default_engine: Optional[str] = DEFAULTS["default_engine"]

    # Runtime-only settings (not saved to file)
    _source: str = field(default="defaults", repr=False)

    @classmethod
    def load(cls) -> "TTSAppConfig":
        """Load configuration from file, falling back to defaults."""
        if not CONFIG_FILE.exists():
            return cls(_source="defaults")

        try:
            with open(CONFIG_FILE, "r") as f:
                data = yaml.safe_load(f) or {}

            config = cls(_source="file")
            for key, value in data.items():
                if hasattr(config, key) and not key.startswith("_"):
                    setattr(config, key, value)

            return config
        except (OSError, yaml.YAMLError):
            return cls(_source="defaults (error)")

    def save(self) -> bool:
        """Save configuration to file."""
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

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {k: v for k, v in asdict(self).items() if not k.startswith("_")}

    @staticmethod
    def get_config_path() -> Path:
        """Return the config file path."""
        return CONFIG_FILE

    @staticmethod
    def reset() -> bool:
        """Delete configuration file, reverting to defaults."""
        try:
            if CONFIG_FILE.exists():
                CONFIG_FILE.unlink()
            return True
        except OSError:
            return False


def generate_sample_config() -> str:
    """Generate a sample configuration file content."""
    sample = """# TTS Application Configuration
# Save this file to ~/.config/tts/config.yaml

# Language: en-us, en-uk, ta
language: en-us

# Speed: slow, normal, fast
speed: normal

# Enable audio caching
cache_enabled: true

# Maximum cache size in megabytes
cache_max_size_mb: 500

# Show verbose output
verbose: false

# Show desktop notifications
notifications: true

# Show progress for long texts
progress: true

# Preferred engine: edge, gtts, espeak (null = auto)
default_engine: null
"""
    return sample
