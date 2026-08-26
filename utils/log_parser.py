#!/usr/bin/env python3
"""
log_parser.py — Detects log source (nginx, hdfs, or generic) and
parses each line into a ParsedLog dataclass using regex patterns.

Usage:
    python log_parser.py path/to/logfile.log
    python log_parser.py path/to/logfile.log --format nginx   # force a format
    cat file.log | python log_parser.py -                     # read stdin

Output: JSON lines, one parsed record per input line.
"""

import argparse
import json
import re
import sys
from dataclasses import asdict
from datetime import datetime
from typing import Any

from models.log import ParsedLog

# ---------------------------------------------------------------------------
# Regex patterns for each log format
# ---------------------------------------------------------------------------

PATTERNS: dict[str, re.Pattern] = {
    # Nginx combined log format:
    # 127.0.0.1 - - [21/Aug/2026:10:00:00 +0000] "GET /index.html HTTP/1.1" 200 612 "-" "Mozilla/5.0"
    "nginx": re.compile(
        r"^(?P<remote_addr>\S+) - (?P<remote_user>\S+) "
        r"\[(?P<time>[^\]]+)\] "
        r'"(?P<method>\S+) (?P<path>\S+) (?P<protocol>[^"]+)" '
        r"(?P<status>\d{3}) (?P<body_bytes>\d+|-) "
        r'"(?P<referer>[^"]*)" "(?P<user_agent>[^"]*)"'
    ),
    # HDFS log format (Hadoop standard log4j pattern):
    # 2026-08-21 10:00:00,123 INFO dfs.DataNode$PacketResponder: PacketResponder 1 for block blk_123 terminating
    "hdfs": re.compile(
    r"^(?P<date>\d{6})\s+(?P<time>\d{6})\s+(?P<thread>\d+)\s+"
    r"(?P<level>[A-Z]+)\s+(?P<component>[^:]+):\s+(?P<message>.*)$"
), 
    # Generic fallback: "YYYY-MM-DD HH:MM:SS LEVEL message..."
    # 2026-08-21 10:00:00 ERROR something went wrong
    "generic": re.compile(
        r"^(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) "
        r"(?P<level>[A-Z]+) (?P<message>.*)$"
    ),
}

# Order matters: more specific formats are tried before generic fallback.
DETECTION_ORDER: list[str] = ["nginx", "hdfs", "generic"]


# ---------------------------------------------------------------------------
# Core parsing logic
# ---------------------------------------------------------------------------


def detect_and_parse(line: str) -> tuple[str, dict[str, Any] | None]:
    """
    Try each known pattern in order and return (source, parsed_fields).
    If nothing matches, source is 'unknown' and parsed_fields is None.
    """
    for source in DETECTION_ORDER:
        match = PATTERNS[source].match(line)
        if match:
            return source, match.groupdict()
    return "unknown", None


def parse_line(line: str, forced_format: str | None = None) -> dict[str, Any]:
    """
    Parse a single line into a raw dict:
        {"source": ..., "raw": ..., "parsed": dict|None, "matched": bool}

    NOTE: `parsed` is None whenever nothing matched (or the forced format
    didn't match). Callers must handle that — see `to_parsed_log` below,
    which is the supported way to turn this into a ParsedLog.
    """
    line = line.rstrip("\n")

    if forced_format:
        pattern = PATTERNS.get(forced_format)
        if pattern is None:
            raise ValueError(f"Unknown format: {forced_format}")
        match = pattern.match(line)
        source = forced_format
        fields = match.groupdict() if match else None
    else:
        source, fields = detect_and_parse(line)

    return {
        "source": source,
        "raw": line,
        "parsed": fields,  # None if no pattern matched
        "matched": fields is not None,
    }


# ---------------------------------------------------------------------------
# Conversion: raw parse_line() dict -> ParsedLog
# ---------------------------------------------------------------------------

# nginx's Apache-style timestamp, e.g. "21/Aug/2026:10:00:00 +0000"
_NGINX_TIME_FMT = "%d/%b/%Y:%H:%M:%S %z"


def _nginx_level_from_status(status: str | None) -> str:
    """nginx access logs don't carry a log level, so derive one from the
    HTTP status code as a reasonable stand-in."""
    try:
        code = int(status)
    except (TypeError, ValueError):
        return "INFO"
    if code >= 500:
        return "ERROR"
    if code >= 400:
        return "WARN"
    return "INFO"


def to_parsed_log(record: dict[str, Any]) -> ParsedLog:
    """
    Convert a parse_line() result into a ParsedLog dataclass instance.

    Handles the `parsed is None` case (unmatched / unknown lines) by
    falling back to the current time, an "UNKNOWN" level, and the raw
    line as the message — so downstream code always gets a valid
    ParsedLog and never has to check for None itself.
    """
    source = record["source"]
    raw = record["raw"]
    fields = record["parsed"]

    if fields is None:
        return ParsedLog(
            timestamp=datetime.now(),
            level="UNKNOWN",
            message=raw,
            source=source,
            raw=raw,
            metadata={},
        )

    if source == "nginx":
        try:
            timestamp = datetime.strptime(fields["time"], _NGINX_TIME_FMT)
        except ValueError:
            timestamp = datetime.now()
        level = _nginx_level_from_status(fields.get("status"))
        message = (
            f"{fields.get('method')} {fields.get('path')} -> {fields.get('status')}"
        )
        metadata = {k: v for k, v in fields.items() if k != "time"}

  
    elif source == "hdfs":
        try:
            timestamp = datetime.strptime(
                f"{fields['date']} {fields['time']}",
                "%y%m%d %H%M%S"   # 081109 203615
            )
        except ValueError:
            timestamp = datetime.now()
        level = fields.get("level", "UNKNOWN")
        message = fields.get("message", raw)
        metadata = {"component": fields.get("component", ""), "thread": fields.get("thread", "")}

    elif source == "generic":
        try:
            timestamp = datetime.strptime(
                f"{fields['date']} {fields['time']}", "%Y-%m-%d %H:%M:%S"
            )
        except ValueError:
            timestamp = datetime.now()
        level = fields.get("level", "UNKNOWN")
        message = fields.get("message", raw)
        metadata = {
            k: v
            for k, v in fields.items()
            if k not in ("date", "time", "level", "message")
        }

    else:
        timestamp = datetime.now()
        level = "UNKNOWN"
        message = raw
        metadata = dict(fields)

    return ParsedLog(
        timestamp=timestamp,
        level=level,
        message=message,
        source=source,
        raw=raw,
        metadata=metadata,
    )


def parse_line_to_log(line: str, forced_format: str | None = None) -> ParsedLog:
    """Convenience: parse a line straight into a ParsedLog."""
    return to_parsed_log(parse_line(line, forced_format))


def parse_file(path: str, forced_format: str | None = None) -> list[ParsedLog]:
    results: list[ParsedLog] = []

    if path == "-":
        for line in sys.stdin:
            line = line.strip("\n")
            if not line.strip():
                continue
            results.append(parse_line_to_log(line, forced_format))
    else:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip("\n")
                if not line.strip():
                    continue
                results.append(parse_line_to_log(line, forced_format))

    return results


def _parsed_log_to_json(log: ParsedLog) -> str:
    d = asdict(log)
    d["timestamp"] = log.timestamp.isoformat()
    return json.dumps(d)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Parse logs from nginx, hdfs, or generic format."
    )
    parser.add_argument("logfile", help="Path to log file, or '-' for stdin")
    parser.add_argument(
        "--format",
        choices=list(PATTERNS.keys()),
        default=None,
        help="Force a specific format instead of auto-detecting per line",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output instead of one-line-per-record",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a source-count summary at the end (to stderr)",
    )
    args = parser.parse_args()

    records = parse_file(args.logfile, args.format)

    for rec in records:
        if args.pretty:
            d = asdict(rec)
            d["timestamp"] = rec.timestamp.isoformat()
            print(json.dumps(d, indent=2))
        else:
            print(_parsed_log_to_json(rec))

    if args.summary:
        counts: dict[str, int] = {}
        for rec in records:
            counts[rec.source] = counts.get(rec.source, 0) + 1
        print("\n--- Summary ---", file=sys.stderr)
        for src, count in counts.items():
            print(f"{src}: {count}", file=sys.stderr)


if __name__ == "__main__":
    main()
