from __future__ import annotations

import argparse
import json
import sys

from .logging_utils import configure_logging
from .service import scrape_domain


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vangrondwelle",
        description="Scrape Dutch healthcare provider websites for basic contact details.",
    )
    parser.add_argument(
        "domains",
        nargs="+",
        help="One or more provider domains, for example ziekenhuis.nl or https://www.zorginstelling.nl.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose structured logs on stderr.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    configure_logging(args.verbose)

    results = [scrape_domain(domain).to_dict() for domain in args.domains]
    json.dump(results, sys.stdout, indent=2 if args.pretty else None)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
