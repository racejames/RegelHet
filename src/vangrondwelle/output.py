from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

from .models import ContactInfo

CSV_HEADERS = [
    "provider_name",
    "website_url",
    "domain",
    "directory_source",
    "directory_detail_url",
    "source_url",
    "address",
    "phone",
    "email",
    "confidence",
    "notes",
]


def write_results(results: list[ContactInfo], output_format: str, output_path: str | None, pretty: bool) -> None:
    if output_format == "csv":
        payload = serialize_csv(results)
    else:
        payload = serialize_json(results, pretty=pretty)

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(payload, encoding="utf-8", newline="")
        return

    sys.stdout.write(payload)
    if not payload.endswith("\n"):
        sys.stdout.write("\n")


def serialize_json(results: list[ContactInfo], *, pretty: bool) -> str:
    return json.dumps([result.to_dict() for result in results], indent=2 if pretty else None)


def serialize_csv(results: list[ContactInfo]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_HEADERS)
    writer.writeheader()
    for result in results:
        writer.writerow(
            {
                "provider_name": result.provider_name or "",
                "website_url": result.website_url or "",
                "domain": result.domain,
                "directory_source": result.directory_source or "",
                "directory_detail_url": result.directory_detail_url or "",
                "source_url": result.source_url or "",
                "address": result.address or "",
                "phone": result.phone or "",
                "email": result.email or "",
                "confidence": f"{result.confidence:.2f}",
                "notes": " | ".join(result.notes),
            }
        )
    return buffer.getvalue()
