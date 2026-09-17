"""
Output formatter utility for the AWS Object Storage Universal Extension.

Provides functions that transform raw S3 object data into human-readable
strings suitable for STDOUT table display: byte-count → size string,
timezone-aware datetime → ISO 8601 UTC string, and list-of-rows → ASCII
table via tabulate.
"""
import logging
from datetime import datetime, timezone
from typing import Any

from tabulate import tabulate

logger = logging.getLogger("UNV")

# Size thresholds in bytes.
_KB: int = 1_024
_MB: int = 1_048_576
_GB: int = 1_073_741_824
_TB: int = 1_099_511_627_776


def format_size(size_bytes: int) -> str:
    """
    Convert a raw byte count to a human-readable size string.

    Scaling rules:
        < 1 024             → "{N} B"
        < 1 048 576         → "{N:.1f} KB"
        < 1 073 741 824     → "{N:.1f} MB"
        < 1 099 511 627 776 → "{N:.1f} GB"
        otherwise           → "{N:.1f} TB"

    Args:
        size_bytes: File size in bytes (non-negative integer).

    Returns:
        Human-readable size string with unit suffix.

    Examples:
        >>> format_size(512)
        '512 B'
        >>> format_size(46694)
        '45.6 KB'
        >>> format_size(1258291)
        '1.2 MB'
    """
    logger.debug("Formatting size: %d bytes", size_bytes)
    if size_bytes < _KB:
        return f"{size_bytes} B"
    if size_bytes < _MB:
        return f"{size_bytes / _KB:.1f} KB"
    if size_bytes < _GB:
        return f"{size_bytes / _MB:.1f} MB"
    if size_bytes < _TB:
        return f"{size_bytes / _GB:.1f} GB"
    return f"{size_bytes / _TB:.1f} TB"


def format_timestamp(last_modified: datetime) -> str:
    """
    Convert a timezone-aware datetime to an ISO 8601 UTC string.

    Normalises to UTC regardless of the datetime object's original
    timezone, then formats as "YYYY-MM-DDTHH:MM:SSZ".

    Args:
        last_modified: Timezone-aware datetime (as returned by boto3
                       for the LastModified field of an S3 object).

    Returns:
        ISO 8601 UTC string in the format "YYYY-MM-DDTHH:MM:SSZ".

    Examples:
        >>> from datetime import timezone
        >>> dt = datetime(2024, 1, 15, 10, 23, 0, tzinfo=timezone.utc)
        >>> format_timestamp(dt)
        '2024-01-15T10:23:00Z'
    """
    logger.debug("Formatting timestamp: %s", last_modified)
    utc_dt = last_modified.astimezone(timezone.utc)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def build_ascii_table(rows: list[dict[str, Any]]) -> str:
    """
    Generate a formatted ASCII table from a list of S3 object display rows.

    Each row dict must contain:
        key           (str) — S3 object key
        size          (str) — human-readable size (from format_size)
        last_modified (str) — ISO 8601 UTC string (from format_timestamp)

    The table is generated using tabulate with tablefmt="rounded_outline"
    and the column headers ["Object Key", "Size", "Last Modified"].

    Args:
        rows: List of dicts with keys "key", "size", and "last_modified".

    Returns:
        Formatted ASCII table string ready for printing to STDOUT.
    """
    logger.debug("Building ASCII table for %d rows", len(rows))
    table_data = [
        [row["key"], row["size"], row["last_modified"]]
        for row in rows
    ]
    table_str = tabulate(
        table_data,
        headers=["Object Key", "Size", "Last Modified"],
        tablefmt="rounded_outline",
    )
    logger.debug("ASCII table generated (%d characters)", len(table_str))
    return table_str
