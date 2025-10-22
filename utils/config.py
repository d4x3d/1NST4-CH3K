"""
Configuration Module

This module handles configuration loading and management
for 1NST4-CH3K.
"""

import os
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CheckerConfig:
    """Configuration for the Instagram checker."""
    # Request settings
    timeout: int = 10
    delay_between_requests: float = 1.0
    max_retries: int = 3

    # Threading settings
    max_threads: int = 5
    requests_per_second: float = 1.0

    # Proxy settings
    proxy_file: Optional[str] = None
    proxy_timeout: int = 5
    rotate_proxies: bool = True

    # Output settings
    output_file: Optional[str] = None
    output_format: str = "json"  # json, csv, txt

    # Display settings
    show_colors: bool = True
    show_progress: bool = True
    verbose: bool = False

    # Advanced settings
    user_agent_rotation: bool = True
    rate_limit_adaptive: bool = True


@dataclass
class Config:
    """Main configuration class."""
    checker: CheckerConfig = field(default_factory=CheckerConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Create config from dictionary."""
        checker_data = data.get('checker', {})
        return cls(
            checker=CheckerConfig(**checker_data)
        )

    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'Config':
        """Load config from YAML file."""
        try:
            with open(yaml_path, 'r') as f:
                data = yaml.safe_load(f)
                return cls.from_dict(data)
        except FileNotFoundError:
            return cls()
        except Exception as e:
            print(f"Warning: Error loading config from {yaml_path}: {e}")
            return cls()

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'checker': {
                field.name: getattr(self.checker, field.name)
                for field in self.checker.__dataclass_fields__.values()
            }
        }

    def save_to_yaml(self, yaml_path: str):
        """Save config to YAML file."""
        try:
            os.makedirs(os.path.dirname(yaml_path), exist_ok=True)
            with open(yaml_path, 'w') as f:
                yaml.dump(self.to_dict(), f, default_flow_style=False, indent=2)
        except Exception as e:
            print(f"Error saving config to {yaml_path}: {e}")


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from file or create default.

    Args:
        config_path: Path to config file (optional)

    Returns:
        Config object
    """
    if config_path:
        return Config.from_yaml(config_path)

    # Try to load from default locations
    default_paths = [
        "config.yaml",
        "config.yml",
        os.path.expanduser("~/.1nst4-ch3k/config.yaml"),
        os.path.expanduser("~/.config/1nst4-ch3k/config.yaml")
    ]

    for path in default_paths:
        if os.path.exists(path):
            return Config.from_yaml(path)

    # Return default config
    return Config()


def create_default_config(config_path: str = "config.yaml"):
    """Create a default configuration file."""
    config = Config()
    config.save_to_yaml(config_path)
    print(f"Created default config file: {config_path}")


def get_config_paths() -> Dict[str, str]:
    """Get standard configuration file paths."""
    return {
        "local": "config.yaml",
        "home": os.path.expanduser("~/.1nst4-ch3k/config.yaml"),
        "system": os.path.expanduser("~/.config/1nst4-ch3k/config.yaml")
    }