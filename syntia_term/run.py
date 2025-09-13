import sys
from pathlib import Path

from syntia_term.app import Syntia


def run_syntia():
    root_directory = Path(sys.argv[1])
    if not root_directory.exists():
        raise FileNotFoundError(f"Root directory {root_directory} does not exist")
    elif not root_directory.is_dir():
        root_directory = root_directory.parent

    app = Syntia(root_directory=root_directory)
    app.run()
