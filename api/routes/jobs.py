"""Upload jobs and history management routes."""
import json
import os
import threading
import uuid
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

from api.auth import require_auth
from api.extensions import logger
from api.services.manager_service import get_classes, get_upload_queue
from api.services.uploader_service import (
    calculate_schedule_delay,
    start_upload_thread,
    broadcast_progress,
    cancel_job_timers,
    track_job_timer,
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
    upload_folder = Path(current_app.config.get('UPLOAD_FOLDER', Path.cwd() / 'uploads'))
    upload_folder.mkdir(parents=True, exist_ok=True)

    if request.is_json:
        data = request.json or {}
        video_path = data.get('video_path')
        metadata_path = data.get('metadata_path')
        thumbnail_path = data.get('thumbnail_path')
        metadata = data.get('metadata') or {}
        schedule = data.get('schedule')
        priority = data.get('priority', 'normal')
        channel_id = data.get('channel_id')
        template_id = data.get('template_id')
    else:
        data = request.form.to_dict()
        schedule = data.get('schedule')
        priority = data.get('priority', 'normal')
        channel_id = data.get('channel_id')
        template_id = data.get('template_id')

        meta_raw = data.get('metadata')
        metadata = {}
        if meta_raw:
            try:
                metadata = json.loads(meta_raw) if isinstance(meta_raw, str) else meta_raw
            except Exception:
                pass

        video_path = None
        if 'video' in request.files and request.files['video'].filename:
            v_file = request.files['video']
            safe_v_name = f"{uuid.uuid4().hex[:8]}_{secure_filename(v_file.filename)}"
            saved_v_path = str(upload_folder / safe_v_name)
            v_file.save(saved_v_path)
            video_path = saved_v_path
        elif data.get('video_path'):
            video_path = data.get('video_path')

        metadata_path = None
        if 'metadata_file' in request.files and request.files['metadata_file'].filename:
            m_file = request.files['metadata_file']
            safe_m_name = f"{uuid.uuid4().hex[:8]}_{secure_filename(m_file.filename)}"
            saved_m_path = str(upload_folder / safe_m_name)
            m_file.save(saved_m_path)
            metadata_path = saved_m_path
        elif data.get('metadata_path'):
            metadata_path = data.get('metadata_path')

        thumbnail_path = None
        if 'thumbnail' in request.files and request.files['thumbnail'].filename:
            t_file = request.files['thumbnail']
            safe_t_name = f"{uuid.uuid4().hex[:8]}_{secure_filename(t_file.filename)}"
            saved_t_path = str(upload_folder / safe_t_name)
            t_file.save(saved_t_path)
            thumbnail_path = saved_t_path
        elif data.get('thumbnail_path'):
            thumbnail_path = data.get('thumbnail_path')

    if not video_path or not os.path.exists(video_path):
        return jsonify({"error": "Video file not found"}), 400

    if metadata_path and not os.path.exists(metadata_path):
        return jsonify({"error": "Metadata file not found"}), 400

    if thumbnail_path and not os.path.exists(thumbnail_path):
        return jsonify({"error": "Thumbnail file not found"}), 400

    _, UploadJob, UploadStatus, _, _, _, _, _, _, _, _, _, _, _ = get_classes()
    job = UploadJob(
        video_path=video_path,
        metadata_path=metadata_path,
        thumbnail_path=thumbnail_path,
        schedule=schedule,
        priority=priority,
        channel_id=channel_id,
        template_id=template_id,
        metadata=metadata
    )

    queue = get_upload_queue()
    queue.add_job(job)
    logger.info(f"Created upload job {job.job_id} for {video_path}")

    if schedule:
        job.status = UploadStatus.SCHEDULED
        delay = calculate_schedule_delay(schedule)
        timer = threading.Timer(delay, start_upload_thread, args=[job.job_id])
        timer.daemon = True
        track_job_timer(job.job_id, timer)
        timer.start()
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
        if job.metadata is None:
            job.metadata = {}
        job.metadata['cancelled'] = True
        cancel_job_timers(job_id)
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
        if job.retry_count >= job.max_retries:
            return jsonify({"error": "Max retries reached"}), 400
        job.status = UploadStatus.PENDING
        job.retry_count += 1
        job.error_message = None
        job.completed_at = None
        job.progress = 0.0
        if isinstance(job.metadata, dict):
            job.metadata.pop('cancelled', None)
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
