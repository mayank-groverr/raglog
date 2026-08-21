from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4
from datetime import datetime
from models.log import ParsedLog


class AlertStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


@dataclass
class Alert:
    log: ParsedLog
    anomaly_score: float
    explanation: str
    channels: list[str]
    # defaults last
    status: AlertStatus = AlertStatus.PENDING
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.now)
