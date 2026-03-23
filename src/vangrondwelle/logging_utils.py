from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            payload["request_id"] = record.request_id
        if hasattr(record, "domain"):
            payload["domain"] = record.domain
        if hasattr(record, "url"):
            payload["url"] = record.url
        if hasattr(record, "status_code"):
            payload["status_code"] = record.status_code
        if hasattr(record, "provider"):
            payload["provider"] = record.provider
        if hasattr(record, "location"):
            payload["location"] = record.location
        if hasattr(record, "business_name"):
            payload["business_name"] = record.business_name
        if hasattr(record, "scenario"):
            payload["scenario"] = record.scenario
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


def configure_logging(verbose: bool) -> None:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG if verbose else logging.WARNING)
