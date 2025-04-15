import os
import shutil
import subprocess
from pathlib import Path
import os
import sys

__version__ = "0.3.11"
ROOT_DIR: str = os.path.abspath(os.getenv("ROOT_DIR", os.path.dirname(sys.argv[0])))

CACHE_FOLDER = Path(os.path.join(ROOT_DIR, "data/cache"))


def get_cache_file_path(filename: str, sub_folder: str | None = None) -> Path:
    if sub_folder is not None:
        sub_folder = sub_folder.strip("/")
        sub_folder_path = CACHE_FOLDER / sub_folder
        sub_folder_path.mkdir(parents=True, exist_ok=True)
        return sub_folder_path / filename
    return CACHE_FOLDER / filename


try:
    git_path = shutil.which("git")
    if git_path is None:
        raise FileNotFoundError("git executable not found")
    two_parent = Path(__file__).resolve().parent.parent
    md_ = two_parent / "docs" / "README.md"
    if two_parent.name == "site-packages" or not md_.exists():
        print("not in git repo")
        raise FileNotFoundError("not in git repo")
    WATERMARK_VERSION = (
        subprocess.check_output(  # noqa: S603
            [git_path, "describe", "--always"],
            cwd=Path(__file__).resolve().parent,
        )
        .strip()
        .decode()
    )
except (OSError, FileNotFoundError, subprocess.CalledProcessError):
    WATERMARK_VERSION = f"v{__version__}"

TIKTOKEN_CACHE_FOLDER = CACHE_FOLDER / "tiktoken"
TIKTOKEN_CACHE_FOLDER.mkdir(parents=True, exist_ok=True)
os.environ["TIKTOKEN_CACHE_DIR"] = str(TIKTOKEN_CACHE_FOLDER)
