import json
import logging

from vangrondwelle.logging_utils import JsonFormatter, configure_logging


def test_json_formatter_includes_business_comparison_metadata() -> None:
    record = logging.makeLogRecord(
        {
            "name": "vangrondwelle.business_sources",
            "levelno": logging.INFO,
            "levelname": "INFO",
            "msg": "Fetching business from OSM.",
            "provider": "osm",
            "location": "Bunnik",
            "business_name": "Installatieburo Hevi BV",
            "scenario": "Open source",
        }
    )

    payload = json.loads(JsonFormatter().format(record))

    assert payload["provider"] == "osm"
    assert payload["location"] == "Bunnik"
    assert payload["business_name"] == "Installatieburo Hevi BV"
    assert payload["scenario"] == "Open source"


def test_configure_logging_hides_info_logs_without_verbose(capsys) -> None:
    configure_logging(False)

    logging.getLogger("vangrondwelle.test").info("This should stay hidden.")

    captured = capsys.readouterr()

    assert captured.err == ""
