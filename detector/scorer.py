from detector.statistical import Statistical
from detector.ml_model import MLModel
from models.scored_log import ScoredLog
from models.log import ParsedLog


class Score:
    def __init__(
        self, statistical: Statistical, ml_model: MLModel, threshold: float = 0.6
    ):
        self.statistical = statistical
        self.ml_model = ml_model
        self.threshold = threshold

    def score(self, stat_score: float, ml_score: float) -> float:
        weighted_score = 0.4 * stat_score + 0.6 * ml_score
        return weighted_score

    def is_anomaly(self, score: float, threshold: float = 0.6) -> bool:
        return score >= threshold

    def evaluate(self, log: ParsedLog, stats: dict) -> ScoredLog:
        stat_score = self.statistical.analyze(stats) or 0.0  # handle None
        ml_score = self.ml_model.score(stats)
        combined = self.score(stat_score, ml_score)
        return ScoredLog(log=log, score=combined, is_anomaly=self.is_anomaly(combined))
