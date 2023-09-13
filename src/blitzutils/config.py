from pathlib import Path

CONFIG_FILE: str = "blitzstats.ini"

CONFIG_FILES: list[Path] = [
    Path(".") / CONFIG_FILE,
    Path(__file__).parent / CONFIG_FILE,
    Path.home() / f".{CONFIG_FILE}",
    Path.home() / ".config" / CONFIG_FILE,
    Path.home() / ".config/blitzstats/config",
]


def get_config_file() -> Path | None:
    """Get config file from the default locations"""
    config_file: Path | None = None
    for config_file in CONFIG_FILES:
        if config_file.is_file():
            break
    return config_file
