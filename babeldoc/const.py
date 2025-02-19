import re
from pathlib import Path

CACHE_FOLDER = Path.home() / ".cache" / "babeldoc"


def get_cache_file_path(filename):
    return CACHE_FOLDER / filename


COLOR_PATTERN = r"sc|scn|g|rg|k|cs|gs|ri"
LINE_PATTERN = r"w|j|M|d|i"

COLOR_RE = re.compile(f"^({COLOR_PATTERN})$", re.IGNORECASE)
LINE_RE = re.compile(f"^({LINE_PATTERN})$", re.IGNORECASE)

PASSTHROUGH_PER_CHAR_PATTERN = re.compile(
    f"^({COLOR_PATTERN}|{LINE_PATTERN})$",
    re.IGNORECASE,
)
