"""Bulk multi-channel upload executor: fans out video x channel pairs into the existing queue."""
import threading
from datetime import datetime

from api.extensions import logger
from api.services.manager_service import get_classes, get_upload_queue, get_channel_manager
from api.services.uploader_service import start_upload_thread, broadcast_progress

# ponytail: in-process registry, not persisted — batch recovery = re-submit. Add DB table when crash-recovery needed.
_batches = {}


def create_bulk_batch(video_paths, channel_ids, metadata=None, priority="normal"):
    """Create one upload job per video x channel pair, start workers."""
    if not video_paths or not channel_ids:
        raise ValueError("video_paths and channel_ids required")

    _, UploadJob, UploadStatus, _, _, UploadQueue, ChannelManager, _, _, _, _, _, _, _ = get_classes()
    channel_manager = get_channel_manager()
    queue = get_upload_queue()

    # resolve channels -> accounts (each channel belongs to an account with OAuth creds)
    valid = []
    for cid in channel_ids:
        ch = channel_manager.get_channel(cid)
        if ch:
            valid.append(ch)
    if not valid:
        raise ValueError("no valid channels")

    batch_id = str(__import__("uuid").uuid4())
    jobs = []
    for video_path in video_paths:
        for ch in valid:
            job = UploadJob(
                video_path=video_path,
                channel_id=ch.channel_id,
                priority=priority,
            )
            if metadata:
                job.template_id = metadata.get("template_id")
            queue.add_job(job)
            jobs.append(job)

    _batches[batch_id] = {
        "batch_id": batch_id,
        "jobs": [str(j.job_id) for j in jobs],
        "channel_ids": channel_ids,
        "video_paths": video_paths,
        "created_at": datetime.now().isoformat(),
        "status": "running",
    }

    for j in jobs:
        threading.Thread(target=start_upload_thread, args=[str(j.job_id)], daemon=True).start()

    logger.info(f"Bulk batch {batch_id}: {len(video_paths)} videos x {len(valid)} channels = {len(jobs)} jobs")
    return _batches[batch_id]


def get_bulk_status(batch_id):
    """Aggregate per-job status into batch progress."""
    batch = _batches.get(batch_id)
    if not batch:
        return None
    queue = get_upload_queue()
    _, _, UploadStatus, _, _, _, _, _, _, _, _, _, _, _ = get_classes()
    details = []
    for jid in batch["jobs"]:
        job = queue.get_job(jid)
        if job:
            details.append({
                "job_id": jid,
                "video_path": job.video_path,
                "channel_id": job.channel_id,
                "status": job.status.value,
                "progress": job.progress,
                "video_id": job.video_id,
                "error_message": job.error_message,
            })
    counts = {}
    for d in details:
        counts[d["status"]] = counts.get(d["status"], 0) + 1
    total = len(details)
    done = counts.get("completed", 0) + counts.get("failed", 0) + counts.get("cancelled", 0)
    if done == total and total:
        batch["status"] = "completed" if not counts.get("failed") else "completed_with_errors"
    return {
        **batch,
        "total_jobs": total,
        "counts": counts,
        "done": done,
        "jobs": details,
    }


def get_all_bulk_batches():
    return [get_bulk_status(b["batch_id"]) for b in _batches.values()]