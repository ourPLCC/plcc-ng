import importlib.metadata
from importlib.metadata import PackageNotFoundError


def get_version() -> str:
    try:
        return importlib.metadata.version("plcc-ng")
    except PackageNotFoundError:
        return "unknown"


def main():
    print(f"plcc-ng {get_version()}")
