"""
ml_model.py — runtime inference for the ML anomaly detector.

Loads the IsolationForest model saved by trainer.py and scores new
log windows at runtime. Feature extraction must exactly match
trainer.py, so it's imported from there instead of re-implemented.

Usage:
    from detector.ml_model import MLModel

    model = MLModel.load("detector/model.joblib")
    score = model.score(window.get_stats())   # 0.0 (normal) - 1.0 (anomalous)
"""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np

from detector.trainer import extract_features

DEFAULT_MODEL_PATH = Path("detector/model.joblib")


class ModelNotLoadedError(RuntimeError):
    """Raised when scoring is attempted before a model has been loaded."""


class MLModel:
    """Wraps a trained IsolationForest for fast, repeated scoring."""

    def __init__(self, model=None):
        self._model = model

    @classmethod
    def load(cls, model_path: str | Path = DEFAULT_MODEL_PATH) -> "MLModel":
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(
                f"No trained model found at {model_path}. "
                "Run detector/trainer.py first to produce one."
            )
        model = joblib.load(model_path)
        return cls(model=model)

    def is_loaded(self) -> bool:
        return self._model is not None

    def score(self, stats: dict) -> float:
        """
        Take current window stats (Window.get_stats() output), extract
        the same features used at training time, and return an
        anomaly score in [0.0, 1.0] where higher = more anomalous.
        """
        if self._model is None:
            raise ModelNotLoadedError("Call MLModel.load(...) before scoring.")

        features = extract_features(stats)
        X = np.array(features).reshape(1, -1)

        # decision_function: positive = normal, negative = anomalous.
        # In practice values sit roughly in [-0.5, 0.5], so shifting and
        # flipping maps that range onto ~[0.0, 1.0] with higher = worse.
        raw = float(self._model.decision_function(X)[0])
        score = 0.5 - raw
        return float(np.clip(score, 0.0, 1.0))

    def is_anomaly(self, stats: dict) -> bool:
        """Convenience wrapper around the model's own -1/1 prediction."""
        if self._model is None:
            raise ModelNotLoadedError("Call MLModel.load(...) before scoring.")

        features = extract_features(stats)
        X = np.array(features).reshape(1, -1)
        prediction = self._model.predict(X)[0]  # -1 = anomaly, 1 = normal
        return prediction == -1
