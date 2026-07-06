import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union


def deep_merge(base: dict, overrides: dict) -> dict:
    """Recursively merges two dictionaries, ensuring nested blocks aren't wiped out."""
    for key, value in overrides.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def load_runtime_config(user_config_input: Optional[Union[str, Path, Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Loads internal package defaults and overlays optional user configurations.
    Accepts a file path string, a Path object, or a pre-parsed dictionary.
    """
    # 1. Locate and load package-internal defaults
    package_root = Path(__file__).resolve().parent.parent
    internal_defaults_path = package_root / "config" / "defaults.yml"

    config = {}
    if internal_defaults_path.exists():
        with open(internal_defaults_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

    if not user_config_input:
        return config

    # 2. Parse the user input if it's a file path
    user_overrides = {}
    if isinstance(user_config_input, (str, Path)):
        user_path = Path(user_config_input)
        if user_path.exists():
            with open(user_path, "r", encoding="utf-8") as f:
                user_overrides = yaml.safe_load(f) or {}
        else:
            raise FileNotFoundError(f"Provided configuration file not found at: {user_path}")
    elif isinstance(user_config_input, dict):
        user_overrides = user_config_input

    # 3. Layer the overrides on top of the internal baseline
    return deep_merge(config, user_overrides)