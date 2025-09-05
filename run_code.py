from src.cli import collect_config_interactive
from src.applier import Applier
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def create_data_directories():
    """Checks for the existence of the data directory and its subdirectories,
    and creates them if they don't exist."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    subdirs = ["config", "cookies", "CV"]

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    for subdir in subdirs:
        subdir_path = os.path.join(data_dir, subdir)
        if not os.path.exists(subdir_path):
            os.makedirs(subdir_path)


def run_code():
    create_data_directories()
    config = collect_config_interactive()
    Applier(config).apply()


run_code()
