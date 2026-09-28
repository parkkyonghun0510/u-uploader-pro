import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from .models import UploadJob, UploadStatus


class UploadQueue:
    """Manages the upload queue with priority-based scheduling."""

    def __init__(self):
        self._jobs: dict[str, UploadJob] = {}
        self._history_file = Path.cwd() / 'queue' / 'queue.json'
        self._load_queue()

    def add_job(self, job: UploadJob):
        self._jobs[job.job_id] = job
        self._save_queue()

    def get_job(self, job_id: str) -> Optional[UploadJob]:
        return self._jobs.get(job_id)

    def get_all_jobs(self, status_filter: Optional[str] = None) -> List[UploadJob]:
        jobs = list(self._jobs.values())
        if status_filter:
            jobs = [j for j in jobs if j.status.value == status_filter]
        return sorted(jobs, key=lambda j: self._priority_value(j.priority))

    def get_pending_jobs(self) -> List[UploadJob]:
        return [j for j in self._jobs.values() if j.status in [UploadStatus.PENDING, UploadStatus.SCHEDULED]]

    def remove_job(self, job_id: str):
        self._jobs.pop(job_id, None)
        self._save_queue()

    def clear_completed(self):
        self._jobs = {k: v for k, v in self._jobs.items()
                      if v.status not in [UploadStatus.COMPLETED, UploadStatus.CANCELLED]}
        self._save_queue()

    def get_queue_stats(self) -> dict:
        total = len(self._jobs)
        by_status = {}
        for job in self._jobs.values():
            s = job.status.value
            by_status[s] = by_status.get(s, 0) + 1
        return {
            "total": total,
            "by_status": by_status,
            "pending": by_status.get("pending", 0) + by_status.get("scheduled", 0),
            "in_progress": by_status.get("in_progress", 0),
            "completed": by_status.get("completed", 0),
            "failed": by_status.get("failed", 0)
        }

    def _priority_value(self, priority: str) -> int:
        return {"low": 1, "normal": 2, "high": 3}.get(priority, 2)

    def _save_queue(self):
        self._history_file.parent.mkdir(parents=True, exist_ok=True)
        data = [job.to_dict() for job in self._jobs.values()]
        with open(self._history_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_queue(self):
        if self._history_file.exists():
            try:
                with open(self._history_file) as f:
                    data = json.load(f)
                for item in data:
                    job = UploadJob(
                        video_path=item['video_path'],
                        metadata_path=item.get('metadata_path'),
                        thumbnail_path=item.get('thumbnail_path'),
                        profile_path=item.get('profile_path'),
                        schedule=item.get('schedule'),
                        priority=item.get('priority', 'normal')
                    )
                    job.job_id = item['job_id']
                    job.status = UploadStatus(item['status'])
                    job.progress = item.get('progress', 0.0)
                    job.video_id = item.get('video_id')
                    job.error_message = item.get('error_message')
                    job.created_at = item.get('created_at')
                    job.started_at = item.get('started_at')
                    job.completed_at = item.get('completed_at')
                    job.logs = item.get('logs', [])
                    job.retry_count = item.get('retry_count', 0)
                    job.max_retries = item.get('max_retries', 3)
                    self._jobs[job.job_id] = job
            except Exception:
                pass
