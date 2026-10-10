"""
LLM Request Queue Tracker
Tracks every chat/workflow call that goes through OllamaClient.generate() so
the web UI can show what's queued/running right now, with a progress bar.

Ollama's non-streaming /api/generate only responds once generation is fully
done, so there's no real token-level progress to report. Progress here is an
elapsed-time estimate: elapsed / (rolling average duration for that node+model),
capped below 100% until the call actually finishes.

Concurrency is capped per Ollama node URL (OLLAMA_NODE_CONCURRENCY, default 1 -
matching a single GPU/CPU server processing one generate call at a time), so
extra calls to the same node visibly sit in "queued" state instead of the
queue always being empty.
"""

import os
import time
import uuid
from collections import deque
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

import asyncio

NODE_CONCURRENCY = max(1, int(os.getenv("OLLAMA_NODE_CONCURRENCY", "1")))
DEFAULT_ESTIMATE_SECONDS = float(os.getenv("LLM_QUEUE_DEFAULT_ESTIMATE_SECONDS", "20"))
RETENTION_SECONDS = 15.0  # how long a finished job stays visible in the list
DURATION_SAMPLES = 10  # rolling window used for the per node+model average


class QueueJob:
    def __init__(self, job_type: str, label: str, target_url: str, model: str):
        self.id = str(uuid.uuid4())
        self.job_type = job_type
        self.label = label
        self.target_url = target_url
        self.model = model
        self.status = "queued"
        self.created_at = time.monotonic()
        self.started_at: Optional[float] = None
        self.finished_at: Optional[float] = None
        self.estimated_duration = DEFAULT_ESTIMATE_SECONDS
        self.error: Optional[str] = None

    def to_dict(self) -> Dict:
        now = time.monotonic()

        if self.status == "queued":
            progress = 0
            elapsed = now - self.created_at
        elif self.status == "running":
            elapsed = now - self.started_at
            progress = int(min(95, (elapsed / self.estimated_duration) * 100)) if self.estimated_duration > 0 else 0
        else:
            elapsed = (self.finished_at or now) - (self.started_at or self.created_at)
            progress = 100

        return {
            "id": self.id,
            "type": self.job_type,
            "label": self.label,
            "target": self.target_url,
            "model": self.model,
            "status": self.status,
            "progress": progress,
            "elapsed_seconds": round(elapsed, 1),
            "estimated_seconds": round(self.estimated_duration, 1),
            "error": self.error,
        }


_jobs: Dict[str, QueueJob] = {}
_durations: Dict[str, "deque[float]"] = {}
_semaphores: Dict[str, asyncio.Semaphore] = {}


def _duration_key(target_url: str, model: str) -> str:
    return f"{target_url}|{model}"


def _get_semaphore(target_url: str) -> asyncio.Semaphore:
    sem = _semaphores.get(target_url)
    if sem is None:
        sem = asyncio.Semaphore(NODE_CONCURRENCY)
        _semaphores[target_url] = sem
    return sem


def _estimate_duration(target_url: str, model: str) -> float:
    samples = _durations.get(_duration_key(target_url, model))
    if not samples:
        return DEFAULT_ESTIMATE_SECONDS
    return sum(samples) / len(samples)


def _record_duration(target_url: str, model: str, duration: float) -> None:
    key = _duration_key(target_url, model)
    samples = _durations.setdefault(key, deque(maxlen=DURATION_SAMPLES))
    samples.append(duration)


def _prune() -> None:
    cutoff = time.monotonic() - RETENTION_SECONDS
    stale = [
        job_id for job_id, job in _jobs.items()
        if job.status in ("done", "error") and (job.finished_at or 0) < cutoff
    ]
    for job_id in stale:
        del _jobs[job_id]


@asynccontextmanager
async def track(target_url: str, model: str, job_type: str, label: str):
    """Register a queued->running->done/error job around an Ollama call."""

    _prune()
    job = QueueJob(job_type=job_type, label=label, target_url=target_url or "unknown", model=model or "unknown")
    _jobs[job.id] = job

    async with _get_semaphore(job.target_url):
        job.status = "running"
        job.started_at = time.monotonic()
        job.estimated_duration = _estimate_duration(job.target_url, job.model)

        try:
            yield job
        except Exception as e:
            job.status = "error"
            job.finished_at = time.monotonic()
            job.error = str(e)
            raise
        else:
            job.status = "done"
            job.finished_at = time.monotonic()
            _record_duration(job.target_url, job.model, job.finished_at - job.started_at)


def snapshot() -> List[Dict]:
    """Current queue, oldest first - active jobs plus recently finished ones."""

    _prune()
    return [job.to_dict() for job in sorted(_jobs.values(), key=lambda j: j.created_at)]
