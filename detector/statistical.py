from collections import deque
import numpy as np


class Statistical:
    def __init__(self, maxlen=100):
        self.maxlen = maxlen
        self.history = deque(maxlen=maxlen)

    def update(self, stats: dict):
        self.history.append(stats)

    def calculate_zscore(self, current_value, mean, std_dev):
        if std_dev == 0:
            return 0
        return (current_value - mean) / std_dev

    def analyze(self, stats: dict):
        if len(self.history) < 2:
            self.update(stats)
            return None

        means = {}
        std_devs = {}

        for key in stats:
            values = np.array([s[key] for s in self.history if key in s])

            if len(values) == 0:
                continue

            mean = np.mean(values)
            std_dev = np.std(values)

            if std_dev == 0:
                continue

            means[key] = mean
            std_devs[key] = std_dev

        z_scores = {}
        for key, value in stats.items():
            if key in means:
                z_scores[key] = (value - means[key]) / std_devs[key]

        if not z_scores:
            self.update(stats)
            return 0

        # better: absolute anomaly strength
        zscore = np.mean(np.abs(list(z_scores.values())))
        score = float(np.tanh(zscore / 3))

        self.update(stats)
        return score
