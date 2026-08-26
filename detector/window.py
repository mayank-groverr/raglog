from collections import deque
from datetime import datetime, timedelta

from models.log import ParsedLog


class Window:
    def __init__(self, size=100, time_window=15):
        self.log_queue = deque(maxlen=size)
        self.time_window = timedelta(minutes=time_window)

    def add(self, log: ParsedLog):
        self.log_queue.append(log)
        self.evict_oldest()  # Evict logs outside the time window

    def get_logs(self) -> list[ParsedLog]:
        return list(self.log_queue)

    def get_stats(self) -> dict:
        total_logs = len(self.log_queue)
        error_logs = sum(1 for log in self.log_queue if log.level == "ERROR")
        warn_counts = sum(1 for log in self.log_queue if log.level == "WARN")
        error_rate = error_logs / total_logs if total_logs > 0 else 0
        level_frequencies = {
            "INFO": sum(1 for log in self.log_queue if log.level == "INFO"),
            "WARN": sum(1 for log in self.log_queue if log.level == "WARN"),
            "ERROR": sum(1 for log in self.log_queue if log.level == "ERROR"),
        }
        return {
            "Total Logs": total_logs,
            "Error Logs": error_logs,
            "Warn Counts": warn_counts,
            "Error Rate": error_rate,
            "Level Frequencies": level_frequencies,
        }

    def is_ready(self, min_logs=10) -> bool:
        return len(self.log_queue) >= min_logs

    def evict_oldest(self):
        if not self.log_queue:
            return
        newest = self.log_queue[-1].timestamp
        cutoff = newest - self.time_window   # relative to newest log, not now
        while self.log_queue:
            if self.log_queue[0].timestamp < cutoff:
                self.log_queue.popleft()
            else:
                break
