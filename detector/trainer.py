"""
trainer.py — offline training script for the ML anomaly detector.

Run once (or whenever you want to retrain) on a dataset of *normal*
logs (e.g. the HDFS dataset). It slides a `Window` over the logs,
turns each window's stats into a numeric feature vector, fits an
`IsolationForest` on those vectors, and saves the trained model to
disk with joblib.

`ml_model.py` loads the model this script produces and must build
feature vectors the exact same way -- that's why `extract_features()`
lives here and is imported by ml_model.py rather than duplicated.

Usage:
    python -m detector.trainer --logs path/to/hdfs.log --model-out detector/model.joblib
    python -m detector.trainer --logs path/to/logs_dir/ --format hdfs
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from tqdm import tqdm


import joblib
from sklearn.ensemble import IsolationForest

from detector.window import Window

# NOTE: imported lazily inside build_training_matrix() instead of at module
# level. utils/log_parser.py currently has a pre-existing syntax error
# (`except TypeError, ValueError:`) unrelated to this file; importing it
# eagerly here would break `from detector.trainer import extract_features`
# for anyone (e.g. ml_model.py) who only needs feature extraction and never
# touches file parsing. Fix utils/log_parser.py separately to actually run
# training from log files.

# Order matters: ml_model.py must build vectors with this exact same order.
FEATURE_NAMES = [
    "error_rate",
    "warn_rate",
    "total_logs",
    "error_count",
    "info_freq",
    "warn_freq",
    "error_freq",
]


def extract_features(stats: dict) -> list[float]:
    """
    Turn the dict returned by Window.get_stats() into a fixed-order
    numeric feature vector. Must match FEATURE_NAMES above, and must
    be used identically by both trainer.py and ml_model.py.
    """
    total = stats.get("Total Logs", 0)
    error_count = stats.get("Error Logs", 0)
    warn_count = stats.get("Warn Counts", 0)
    error_rate = stats.get("Error Rate", 0.0)
    warn_rate = (warn_count / total) if total > 0 else 0.0
    level_freq = stats.get("Level Frequencies", {})

    return [
        float(error_rate),
        float(warn_rate),
        float(total),
        float(error_count),
        float(level_freq.get("INFO", 0)),
        float(level_freq.get("WARN", 0)),
        float(level_freq.get("ERROR", 0)),
    ]


def _iter_log_files(logs_path: Path):
    if logs_path.is_dir():
        yield from sorted(p for p in logs_path.iterdir() if p.is_file())
    else:
        yield logs_path


def build_training_matrix(
    logs_path: Path,
    forced_format: str | None = None,
    window_size: int = 100,
    time_window: int = 15,
    min_logs: int = 10,
) -> list[list[float]]:
    """
    Parse the given log file(s), slide a Window across them in order,
    and collect one feature vector per window snapshot once the
    window has enough logs to be "ready".
    """
    from utils.log_parser import parse_file

    window = Window(size=window_size, time_window=time_window)
    features: list[list[float]] = []

    files = list(_iter_log_files(logs_path))
    for file_path in tqdm(files, desc="Files", unit="file"):
        parsed_logs = parse_file(str(file_path), forced_format)
        for log in tqdm(parsed_logs, desc=file_path.name, unit="log", leave=False):
            window.add(log)
            if window.is_ready(min_logs=min_logs):
                features.append(extract_features(window.get_stats()))

    return features 

def train(
    logs_path: Path,
    model_out: Path,
    forced_format: str | None = None,
    window_size: int = 100,
    time_window: int = 15,
    min_logs: int = 10,
    contamination: float = 0.05,
) -> Path:
    features = build_training_matrix(
        logs_path,
        forced_format=forced_format,
        window_size=window_size,
        time_window=time_window,
        min_logs=min_logs,
    )

    if len(features) < 2:
        raise ValueError(
            f"Not enough window samples to train on (got {len(features)}). "
            "Provide a larger normal-log dataset."
        )

    model = IsolationForest(contamination=contamination, random_state=42)
    model.fit(features)

    model_out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_out)

    print(f"Trained IsolationForest on {len(features)} window samples.")
    print(f"Saved model to {model_out}")
    return model_out


def main():
    parser = argparse.ArgumentParser(
        description="Train the log-anomaly IsolationForest model on normal logs."
    )
    parser.add_argument(
        "--logs",
        required=True,
        help="Path to a normal-log file or a directory of log files (e.g. HDFS dataset).",
    )
    parser.add_argument(
        "--model-out",
        default="detector/model.joblib",
        help="Where to save the trained model (default: detector/model.joblib).",
    )
    parser.add_argument(
        "--format",
        dest="forced_format",
        default=None,
        choices=["nginx", "hdfs", "generic"],
        help="Force a specific log format instead of auto-detecting.",
    )
    parser.add_argument("--window-size", type=int, default=100)
    parser.add_argument("--time-window", type=int, default=15, help="Minutes.")
    parser.add_argument("--min-logs", type=int, default=10)
    parser.add_argument(
        "--contamination",
        type=float,
        default=0.05,
        help="Expected fraction of anomalies (default: 0.05).",
    )
    args = parser.parse_args()

    logs_path = Path(args.logs)
    if not logs_path.exists():
        print(f"error: {logs_path} does not exist", file=sys.stderr)
        sys.exit(1)

    train(
        logs_path=logs_path,
        model_out=Path(args.model_out),
        forced_format=args.forced_format,
        window_size=args.window_size,
        time_window=args.time_window,
        min_logs=args.min_logs,
        contamination=args.contamination,
    )


if __name__ == "__main__":
    main()
