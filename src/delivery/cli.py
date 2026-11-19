"""Command line entry point: ``delivery run``."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .pipeline import run


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="delivery")
    sub = parser.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run", help="validate the data, build the model and write all KPI tables")
    r.add_argument("--data", type=Path, default=Path("data/olist"))
    r.add_argument("--out", type=Path, default=Path("reports"))
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    summary = run(args.data, args.out)
    for key, value in summary.items():
        print(f"{key:30s} {value:,.3f}")


if __name__ == "__main__":
    main()
