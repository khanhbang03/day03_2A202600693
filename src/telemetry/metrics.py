import time
from typing import Dict, Any, List
from src.telemetry.logger import logger

class PerformanceTracker:
    """
    Tracking industry-standard metrics for LLMs.
    """
    def __init__(self):
        self.session_metrics = []

    def track_request(self, provider: str, model: str, usage: Dict[str, int], latency_ms: int):
        """
        Logs a single request metric to our telemetry.
        """
        metric = {
            "provider": provider,
            "model": model,
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "latency_ms": latency_ms,
            "cost_estimate": self._calculate_cost(model, usage) # Mock cost calculation
        }
        self.session_metrics.append(metric)
        logger.log_event("LLM_METRIC", metric)

    def _calculate_cost(self, model: str, usage: Dict[str, int]) -> float:
        """
        TODO: Implement real pricing logic.
        For now, returns a dummy constant.
        """
        total_tokens = usage.get("total_tokens")
        if total_tokens is None:
            total_tokens = usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)

        model_key = model.lower()
        pricing_per_1k = {
            "gpt-4": 0.06,
            "gpt-4o": 0.03,
            "gpt-4o-mini": 0.002,
            "gpt-3.5": 0.002,
            "phi-3-mini": 0.001,
            "llama": 0.0005,
            "local": 0.0,
        }

        for key, rate in pricing_per_1k.items():
            if key in model_key:
                return (total_tokens / 1000) * rate

        return (total_tokens / 1000) * 0.01

# Global tracker instance
tracker = PerformanceTracker()
