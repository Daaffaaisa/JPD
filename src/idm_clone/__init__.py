import sys
from .cli import run_cli, build_parser

def main() -> None:
    code = run_cli(sys.argv[1:])
    sys.exit(code)

__all__ = ["main", "run_cli", "build_parser"]
