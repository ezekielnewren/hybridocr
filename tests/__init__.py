import os
from pathlib import Path

dir_test_file_base = Path(__file__).resolve().parent / "file"

def open_test_file(path):
    return open(dir_test_file_base / path, "rb")


def list_test_files():
    for root, dirs, files in os.walk(dir_test_file_base):
        prefix = Path(root).relative_to(dir_test_file_base)
        for v in files:
            yield prefix/v
