"""Application configuration (R7).

22 fields are declared; only 4 are ever read anywhere in the codebase
(max_retries, timeout_seconds, queue_name, log_level — accessed in service.py).
The remaining 18 are speculative / unused and safe to delete.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Config:
    """Application configuration.

    R7 (REMOVABLE fields): 22 fields, but only 4 are accessed anywhere:
    ``max_retries``, ``timeout_seconds``, ``queue_name``, ``log_level``.
    The other 18 were added speculatively and are never read.  They are
    safe to delete without touching any test or runtime behaviour.
    """

    # --- Used fields (4) ---
    max_retries: int = 3
    timeout_seconds: float = 30.0
    queue_name: str = "default"
    log_level: str = "INFO"

    # --- Unused fields (18) — R7: safe to remove ---
    worker_count: int = 4
    heartbeat_interval: int = 10
    shutdown_grace_period: int = 5
    enable_metrics: bool = False
    metrics_port: int = 9090
    enable_tracing: bool = False
    trace_sample_rate: float = 0.01
    max_queue_depth: int = 1000
    dead_letter_queue: str = "dlq"
    retry_backoff_base: float = 2.0
    retry_jitter_ms: int = 100
    db_pool_size: int = 5
    db_connection_timeout: float = 5.0
    cache_ttl_seconds: int = 300
    feature_flag_refresh_interval: int = 60
    audit_log_enabled: bool = False
    cors_origins: list[str] = field(default_factory=list)
    plugin_directories: list[str] = field(default_factory=list)
