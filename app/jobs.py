import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class Job:
    id: str
    status: str = "queued"  # queued | running | succeeded | failed
    prompt: str = ""
    framework: str = "streamlit"
    message: str = ""
    progress: float = 0.0
    zip_path: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class JobStore:
    _lock = threading.Lock()
    _jobs: Dict[str, Job] = {}
    _pruner_started = False

    @classmethod
    def create(cls, prompt: str, framework: str) -> Job:
        job_id = uuid.uuid4().hex
        job = Job(id=job_id, prompt=prompt, framework=framework)
        with cls._lock:
            cls._jobs[job_id] = job
        return job

    @classmethod
    def get(cls, job_id: str) -> Optional[Job]:
        with cls._lock:
            return cls._jobs.get(job_id)

    @classmethod
    def update(cls, job_id: str, **kwargs):
        with cls._lock:
            job = cls._jobs.get(job_id)
            if not job:
                return
            for k, v in kwargs.items():
                setattr(job, k, v)
            job.updated_at = time.time()

    @classmethod
    def set_progress(cls, job_id: str, progress: float, message: str = ""):
        cls.update(job_id, progress=max(0.0, min(1.0, progress)), message=message)

    @classmethod
    def all(cls):
        with cls._lock:
            return list(cls._jobs.values())

    @classmethod
    def start_pruner(cls, ttl_seconds: int = 600, sleep_seconds: int = 30):
        # Remove finished/failed jobs after TTL and delete leftover zips
        if cls._pruner_started:
            return
        cls._pruner_started = True

        def _loop():
            while True:
                now = time.time()
                to_delete = []
                with cls._lock:
                    for jid, job in list(cls._jobs.items()):
                        if job.status in {"succeeded", "failed"} and (now - job.updated_at) > ttl_seconds:
                            to_delete.append(jid)
                for jid in to_delete:
                    job = cls.get(jid)
                    if job and job.zip_path and os.path.exists(job.zip_path):
                        try:
                            os.remove(job.zip_path)
                        except Exception:
                            pass
                    with cls._lock:
                        cls._jobs.pop(jid, None)
                time.sleep(sleep_seconds)

        t = threading.Thread(target=_loop, daemon=True)
        t.start()