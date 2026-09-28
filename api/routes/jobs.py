"""Upload jobs and history management routes."""
import json
import os
import threading
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app

from api.auth import require_auth
from api.extensions import logger
from api.services.manager_service import get_classes, get_upload_queue
from api.services.uploader_service import (
    calculate_schedule_delay,
    start_upload_thread,
    broadcast_progress,
)

jobs_bp = Blueprint('jobs', __name__)


@jobs_bp.route('/api/jobs', methods=['GET'])
@require_auth
def get_jobs():
    """List all upload jobs with optional status and channel filtering."""
    status_filter = request.args.get('status', None)
    channel_filter = request.args.get('channel_id', None)
    queue = get_upload_queue()
    jobs = queue.get_all_jobs(status_filter)
    if channel_filter:
        jobs = [j for j in jobs if getattr(j, 'channel_id', None) == channel_filter]
    return jsonify([job.to_dict() for job in jobs])


@jobs_bp.route('/api/jobs/<job_id>', methods=['GET'])
@require_auth
def get_job(job_id: str):
    """Retrieve details of a single upload job."""
    queue = get_upload_queue()
    job = queue.get_job(job_id)
    if job:
        return jsonify(job.to_dict())
    return jsonify({"error": "Job not found"}), 404


@jobs_bp.route('/api/jobs', methods=['POST'])
@require_auth
def create_job():
    """Create and schedule or start a new video upload job."""
    data = request.json or {}
    video_path = data.get('video_path')
    if not video_path or not os.path.exists(video_path):
        return jsonify({"error": "Video file not found"}), 400

    metadata_path = data.get('metadata_path')
    if metadata_path and not os.path.exists(metadata_path):
        return jsonify({"error": "Metadata file not found"}), 400

    thumbnail_path = data.get('thumbnail_path')
    if thumbnail_path and not os.path.exists(thumbnail_path):
        return jsonify({"error": "Thumbnail file not found"}), 400

    schedule = data.get('schedule')
    priority = data.get('priority', 'normal')
    channel_id = data.get('channel_id')
    template_id = data.get('template_id')

    _, UploadJob, UploadStatus, _, _, _, _, _, _, _, _, _, _, _ = get_classes()
    job = UploadJob(
        video_path=video_path,
        metadata_path=metadata_path,
        thumbnail_path=thumbnail_path,
        schedule=schedule,
        priority=priority,
        channel_id=channel_id,
        template_id=template_id
    )

    queue = get_upload_queue()
    queue.add_job(job)
    logger.info(f"Created upload job {job.job_id} for {video_path}")

    if schedule:
        job.status = UploadStatus.SCHEDULED
        delay = calculate_schedule_delay(schedule)
        threading.Timer(delay, start_upload_thread, args=[job.job_id]).start()
    else:
        job.status = UploadStatus.PENDING
        threading.Thread(target=start_upload_thread, args=[job.job_id], daemon=True).start()

    return jsonify(job.to_dict()), 201


@jobs_bp.route('/api/jobs/<job_id>/cancel', methods=['POST'])
@require_auth
def cancel_job(job_id: str):
    """Cancel a pending, in-progress, or scheduled job."""
    queue = get_upload_queue()
    _, _, UploadStatus, _, _, _, _, _, _, _, _, _, _, _ = get_classes()
    job = queue.get_job(job_id)
    if job and job.status in [UploadStatus.PENDING, UploadStatus.IN_PROGRESS, UploadStatus.SCHEDULED]:
        from datetime import datetime
        job.status = UploadStatus.CANCELLED
        job.completed_at = datetime.now().isoformat()
        broadcast_progress(job_id)
        return jsonify({"message": "Job cancelled"})
    return jsonify({"error": "Cannot cancel job"}), 400


@jobs_bp.route('/api/jobs/<job_id>/retry', methods=['POST'])
@require_auth
def retry_job(job_id: str):
    """Retry a failed upload job."""
    queue = get_upload_queue()
    _, _, UploadStatus, _, _, _, _, _, _, _, _, _, _, _ = get_classes()
    job = queue.get_job(job_id)
    if job and job.status == UploadStatus.FAILED:
        job.status = UploadStatus.PENDING
        job.retry_count += 1
        job.error_message = None
        threading.Thread(target=start_upload_thread, args=[job_id], daemon=True).start()
        return jsonify({"message": "Retry started"})
    return jsonify({"error": "Cannot retry job"}), 400


@jobs_bp.route('/api/history', methods=['GET'])
@require_auth
def get_history():
    """Retrieve historical upload records."""
    logs_dir = Path(current_app.config.get('LOGS_DIR', Path.cwd() / 'logs'))
    history_file = logs_dir / 'upload_history.json'
    if history_file.exists():
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        except Exception:
            return jsonify([])
    return jsonify([])
