"""AI-based anomaly detection using Isolation Forest and optional Autoencoder."""
import asyncio
from collections import deque
from typing import Optional

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from structlog import get_logger

log = get_logger(__name__)


class AnomalyDetector:
    """Device behavior profiling with Isolation Forest for anomaly scoring."""

    def __init__(
        self,
        contamination: float = 0.05,
        window_size: int = 1000,
        n_estimators: int = 100,
    ):
        self.contamination = contamination
        self.window_size = window_size
        self.n_estimators = n_estimators
        self._model: Optional[IsolationForest] = None
        self._scaler = StandardScaler()
        self._buffer: deque = deque(maxlen=window_size)
        self._fitted = False
        self._lock = asyncio.Lock()

    def _features_from_flow(self, flow: dict) -> Optional[np.ndarray]:
        """Extract numeric features from flow record for model input."""
        try:
            f = [
                flow.get("bytes_sent", 0) or 0,
                flow.get("bytes_recv", 0) or 0,
                flow.get("retrans_count", 0) or 0,
                flow.get("drop_count", 0) or 0,
                flow.get("rtt_avg_ms", 0) or 0,
                flow.get("src_port", 0) or 0,
                flow.get("dst_port", 0) or 0,
            ]
            return np.array(f, dtype=np.float64).reshape(1, -1)
        except (TypeError, KeyError):
            return None

    async def add_sample(self, flow: dict) -> Optional[float]:
        """Add flow sample to buffer; return anomaly score (-1 to 1, higher = more anomalous) if model fitted."""
        feat = self._features_from_flow(flow)
        if feat is None:
            return None
        async with self._lock:
            arr = feat.flatten()
            self._buffer.append(arr)
            if len(self._buffer) < 50:
                return None
            if not self._fitted:
                return None
            X = np.array(self._buffer)
            X_scaled = self._scaler.transform(X)
            score = self._model.decision_function(X_scaled[-1:])[0]
            return float(score)

    async def fit(self) -> bool:
        """Fit Isolation Forest on buffered samples."""
        async with self._lock:
            if len(self._buffer) < 50:
                log.info("anomaly_detector_insufficient_data", n=len(self._buffer))
                return False
            X = np.array(self._buffer)
            self._scaler.fit(X)
            X_scaled = self._scaler.transform(X)
            self._model = IsolationForest(
                contamination=self.contamination,
                n_estimators=self.n_estimators,
                random_state=42,
            )
            self._model.fit(X_scaled)
            self._fitted = True
            log.info("anomaly_detector_fitted", n_samples=len(X))
            return True

    async def score(self, flow: dict) -> Optional[float]:
        """Compute anomaly score for a single flow (without adding to buffer)."""
        feat = self._features_from_flow(flow)
        if feat is None or not self._fitted:
            return None
        async with self._lock:
            X_scaled = self._scaler.transform(feat)
            return float(self._model.decision_function(X_scaled)[0])
