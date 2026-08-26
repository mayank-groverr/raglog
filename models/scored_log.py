from dataclasses import dataclass
from models.log import ParsedLog


@dataclass
class ScoredLog:
    log: ParsedLog
    score: float  # combined 0.0-1.0
    is_anomaly: bool  # score >= threshold
