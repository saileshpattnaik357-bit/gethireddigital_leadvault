"""LeadVault AI — Phase 13 Celery & Redis Distributed Broker Configuration.

Implements LV-P13-001 (Celery Worker & Redis Broker) and LV-P13-002 (Celery Beat Scheduler).
Automatically uses Redis when REDIS_URL / CELERY_BROKER_URL is configured, and falls back
to in-memory eager execution when unset so local development and CI run seamlessly.
"""

from __future__ import annotations

import os
from celery import Celery
from kombu import Queue

REDIS_URL = os.getenv("REDIS_URL", "").strip()
BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL or "memory://").strip()
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL or "cache+memory://").strip()
IS_REDIS_CONFIGURED = BROKER_URL.startswith(("redis://", "rediss://"))
HEARTBEAT_INTERVAL_SECONDS = int(os.getenv("MINING_CRON_INTERVAL_SECONDS", "21600"))

celery_app = Celery(
    "leadvault",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=["backend.tasks.mining_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_always_eager=not IS_REDIS_CONFIGURED,
    task_eager_propagates=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_default_queue="p1_mining",
    task_queues=(
        Queue("p0_tier_a", routing_key="p0.#"),
        Queue("p1_mining", routing_key="p1.#"),
        Queue("dead_letter", routing_key="dlq.#"),
    ),
    beat_schedule={
        "scheduled-icp-mining-heartbeat": {
            "task": "leadvault.tasks.scheduled_icp_mining_heartbeat",
            "schedule": float(HEARTBEAT_INTERVAL_SECONDS),
            "options": {"queue": "p1_mining"},
        }
    },
)
