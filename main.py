from pathlib import Path
import os
from typing import Any

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent

DEFAULT_CONFIG: dict[str, Any] = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

app = FastAPI(title="Configuration Precedence API")

# The assignment's checker runs in a browser on a different origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def normalize_key(raw_key: str, *, env_file_layer: bool = False) -> str:
    """Convert a config name to lowercase; strip APP_ prefixes and handle the .env alias."""
    key = raw_key.strip()
    if env_file_layer and key.upper() == "NUM_WORKERS":
        return "workers"
    if key.upper().startswith("APP_"):
        key = key[4:]
    return key.strip().lower()


def coerce_value(key: str, value: Any) -> Any:
    """Apply the assignment's types to known keys and strings to all other keys."""
    if key in {"port", "workers"}:
        return int(value)

    if key == "debug":
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"true", "1", "yes", "on"}

    # Unknown keys and log_level are strings. A blank/null value becomes an empty string.
    return "" if value is None else str(value)


def normalize_layer(values: dict[str, Any], *, env_file_layer: bool = False) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for raw_key, raw_value in values.items():
        if raw_key is None:
            continue
        # APP_ENV selects the YAML file; it is not itself an application config key.
        if str(raw_key).strip().upper() == "APP_ENV":
            continue
        key = normalize_key(str(raw_key), env_file_layer=env_file_layer)
        if key:
            normalized[key] = coerce_value(key, raw_value)
    return normalized


def build_config() -> dict[str, Any]:
    """Merge config in order: defaults < YAML < .env < OS APP_* variables."""
    config = DEFAULT_CONFIG.copy()

    # Read .env without modifying os.environ; that preserves layer precedence.
    env_file_values = dotenv_values(BASE_DIR / ".env")
    environment_name = (
        os.environ.get("APP_ENV")
        or env_file_values.get("APP_ENV")
        or "development"
    ).strip().lower()

    # Layer 2: environment-specific YAML.
    yaml_path = BASE_DIR / f"config.{environment_name}.yaml"
    if yaml_path.exists():
        with yaml_path.open("r", encoding="utf-8") as file:
            yaml_values = yaml.safe_load(file) or {}
        if isinstance(yaml_values, dict):
            config.update(normalize_layer(yaml_values))

    # Layer 3: .env file (APP_* names are also accepted here).
    config.update(normalize_layer(dict(env_file_values), env_file_layer=True))

    # Layer 4: actual OS environment variables with the APP_ prefix.
    os_values: dict[str, str] = {}
    for raw_key, raw_value in os.environ.items():
        if raw_key.upper().startswith("APP_") and raw_key.upper() != "APP_ENV":
            os_values[raw_key] = raw_value
    config.update(normalize_layer(os_values))

    return config


@app.get("/")
def home() -> dict[str, str]:
    return {"message": "Configuration Precedence API is running"}


@app.get("/effective-config")
def effective_config(set_: list[str] = Query(default=[], alias="set")) -> dict[str, Any]:
    config = build_config()

    # Query parameter overrides are the highest-precedence layer.
    for item in set_:
        if "=" not in item:
            continue
        raw_key, raw_value = item.split("=", 1)
        key = normalize_key(raw_key)
        if key:
            config[key] = coerce_value(key, raw_value)

    # Never disclose the actual API key, even if a caller overrides it.
    config["api_key"] = "****"
    return config
