from __future__ import annotations

import argparse

from .business_compare import render_comparison_table
from .business_sources import build_business_comparison
from .logging_utils import configure_logging
from .output import write_results
from .service import scrape_domain, scrape_seeds


def build_domain_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vangrondwelle",
        description="Scrape Dutch healthcare provider websites for basic contact details.",
    )
    parser.add_argument(
        "domains",
        nargs="*",
        help="One or more provider domains, for example ziekenhuis.nl or https://www.zorginstelling.nl.",
    )
    parser.add_argument(
        "--discover-den-haag",
        action="store_true",
        help="Discover organization websites from the public ZorgkaartNederland Den Haag listings and scrape them.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        help="Limit the number of Den Haag directory pages to process during discovery.",
    )
    parser.add_argument(
        "--max-providers",
        type=int,
        help="Limit the number of discovered provider websites to scrape.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "csv"),
        default="json",
        help="Output format.",
    )
    parser.add_argument(
        "--output",
        help="Optional file path for writing the output payload.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=6,
        help="Maximum number of concurrent website scrapes for discovery mode.",
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


def build_compare_business_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vangrondwelle compare-business",
        description="Compare one business across OpenStreetMap, Google Places, and Google Places plus KVK.",
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Business name to compare, for example Installatieburo Hevi BV.",
    )
    parser.add_argument(
        "--location",
        required=True,
        help="Target place for the dry-run, for example Bunnik.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose structured logs on stderr.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)
    if args_list and args_list[0] == "compare-business":
        parser = build_compare_business_parser()
        args = parser.parse_args(args_list[1:])
        configure_logging(args.verbose)
        rows = build_business_comparison(args.name, args.location)
        sys.stdout.write(f"{render_comparison_table(rows)}\n")
        return 0

    parser = build_domain_parser()
    args = parser.parse_args(args_list)
    configure_logging(args.verbose)

    if args.discover_den_haag:
        seeds = discover_den_haag_provider_seeds(
            max_pages=args.max_pages,
            max_providers=args.max_providers,
        )
        results = scrape_seeds(seeds, max_workers=args.workers)
    else:
        if not args.domains:
            parser.error("domains are required unless --discover-den-haag is used")
        results = [scrape_domain(domain) for domain in args.domains]

    write_results(results, output_format=args.format, output_path=args.output, pretty=args.pretty)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
