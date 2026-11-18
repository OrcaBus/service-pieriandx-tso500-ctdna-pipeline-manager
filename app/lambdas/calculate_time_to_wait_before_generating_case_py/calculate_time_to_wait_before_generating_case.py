#!/usr/bin/env python3
"""
Calculate how long to wait before generating the PierianDx case.

PierianDx servers are in New York and every report is stamped with a New York timestamp,
so we wait until every date on the case has passed before creating the case.

Event shape:
{
    "datesList": ["2025-09-25T16:35:48+10:00", "2025-09-24T00:00:00Z", ...]
}

Returns:
{
    "timeToWaitBeforeGeneratingCase": 3600,  # seconds, 0 if all dates are already old enough
    "latestTimestamp": "2025-09-25T16:35:48+10:00"  # latest date in datesList (isoformat)
}

Dates without a timezone are assumed to be UTC.
"""
# Standard imports
from datetime import datetime, timezone
from math import ceil
from typing import Any, Dict, List


def parse_timestamp(timestamp: str) -> datetime:
    """Parse an isoformat timestamp, assuming UTC if no timezone is given"""
    parsed = datetime.fromisoformat(timestamp)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Given a list of timezone aware dates, return the seconds until the latest one
    has passed (0 if it already has), along with the latest date.
    """
    dates_list: List[str] = event.get("datesList") or []

    if len(dates_list) == 0:
        raise ValueError("datesList must contain at least one date")

    latest_timestamp = max(map(parse_timestamp, dates_list))

    seconds_to_wait = (latest_timestamp - datetime.now(timezone.utc)).total_seconds()

    return {
        "timeToWaitBeforeGeneratingCase": max(0, ceil(seconds_to_wait)),
        "latestTimestamp": latest_timestamp.isoformat(),
    }


# if __name__ == "__main__":
#     import json
#
#     print(json.dumps(
#         handler({"datesList": ["2025-09-25T16:35:48+10:00", "2024-10-03T00:00:00Z"]}, None),
#         indent=4
#     ))
