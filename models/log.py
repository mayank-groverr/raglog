from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class LogEntry:
    raw: str
    source: str  # "nginx" / "hdfs" / "docker" / "generic"
    filepath: str
    received_at: datetime = field(default_factory=datetime.now)


@dataclass
class ParsedLog:
    timestamp: datetime
    level: str  # INFO / WARN / ERROR / FATAL
    message: str
    source: str
    raw: str
    metadata: dict = field(default_factory=dict)
