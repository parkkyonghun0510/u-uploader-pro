"""Upload execution, scheduling, history, and real-time progress services."""
import json
import threading
from datetime import datetime
from pathlib import Path
from flask import current_app

from api.extensions import socketio, logger
from .manager_service import (
    get_classes,
    get_upload_queue,
    get_supabase_client,
)


def _get_logs_dir() -> Path:
    """Resolve logs directory path."""
    try:
        if current_app and 'LOGS_DIR' in current_app.config:
            return Path(current_app.config['LOGS_DIR'])
    except RuntimeError:
        pass
    return Path.cwd() / 'logs'


def broadcast_progress(job_id: str):
    """Broadcast upload progress over WebSocket and sync to Supabase."""
    queue = get_upload_queue()
    job = queue.get_job(job_id)
    if job:
        socketio.emit('upload_progress', job.to_dict(), broadcast=True, include_self=False)
        client = get_supabase_client()
        if client:
            threading.Thread(target=_sync_job_to_supabase, args=[job], daemon=True).start()


def _sync_job_to_supabase(job):
    """Sync upload job to Supabase in background."""
    try:
        client = get_supabase_client()
        if client:
            client.update_upload_job(str(job.job_id), {
                'status': job.status.value,
                'progress': job.progress,
                'video_id': getattr(job, 'video_id', None),
                'error_message': getattr(job, 'error_message', None),
                'completed_at': job.completed_at,
            })
    except Exception as e:
        logger.error(f"Supabase sync error: {e}")


def save_job_history(job):
    """Save finished or updated upload job to local JSON history and Supabase."""
    logs_dir = _get_logs_dir()
    logs_dir.mkdir(parents=True, exist_ok=True)
    history_file = logs_dir / 'upload_history.json'
    history = []
    if history_file.exists():
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except Exception:
            history = []
    history.append(job.to_dict())
    try:
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving job history locally: {e}")

    client = get_supabase_client()
    if client:
        threading.Thread(target=_sync_history_to_supabase, args=[job], daemon=True).start()


def _sync_history_to_supabase(job):
    """Sync upload history record to Supabase."""
    try:
        client = get_supabase_client()
        if client:
            client.get_table('upload_history').insert({
                'job_id': str(job.job_id),
                'channel_id': str(job.channel_id) if job.channel_id else None,
                'video_id': getattr(job, 'video_id', None),
                'video_title': getattr(job, 'video_title', None),
                'status': job.status.value,
                'progress': job.progress,
                'duration_seconds': getattr(job, 'duration_seconds', None),
                'file_size': getattr(job, 'file_size', None),
                'error_message': getattr(job, 'error_message', None),
            })
    except Exception as e:
        logger.error(f"History sync error: {e}")


def calculate_schedule_delay(schedule_str: str) -> float:
    """Calculate delay seconds until scheduled upload time."""
    try:
        sched_time = datetime.strptime(schedule_str, "%m/%d/%Y, %H:%M")
        now = datetime.now()
        delay = (sched_time - now).total_seconds()
        return max(delay, 1)
    except Exception:
        return 1.0


def start_upload_thread(job_id: str):
    """Background worker thread to run Selenium YouTube upload."""
    queue = get_upload_queue()
    job = queue.get_job(job_id)
    if not job:
        return

    try:
        YouTubeUploader, _, UploadStatus, _, _, _, _, _, _, _, _, _, _, _ = get_classes()
        job.status = UploadStatus.IN_PROGRESS
        job.started_at = datetime.now().isoformat()
        job.progress = 0.0
        broadcast_progress(job_id)

        uploader = YouTubeUploader(
            video_path=job.video_path,
            metadata_json_path=job.metadata_path,
            thumbnail_path=job.thumbnail_path,
            profile_path=job.profile_path,
            job_id=job_id
        )

        uploader.add_log(f"Starting upload for {job.video_path}")
        if job.channel_id:
            uploader.add_log(f"Target channel: {job.channel_id}")
        was_uploaded, video_id = uploader.upload()

        if was_uploaded:
            job.status = UploadStatus.COMPLETED
            job.video_id = video_id
            job.progress = 100.0
            job.completed_at = datetime.now().isoformat()
            uploader.add_log(f"Upload completed! Video ID: {video_id}")
            logger.info(f"Upload {job_id} completed successfully")
        else:
            job.status = UploadStatus.FAILED
            job.error_message = "Upload was cancelled or failed"
            job.completed_at = datetime.now().isoformat()
            logger.warning(f"Upload {job_id} failed")

    except Exception as e:
        _, _, UploadStatus, _, _, _, _, _, _, _, _, _, _, _ = get_classes()
        job.status = UploadStatus.FAILED
        job.error_message = str(e)
        job.completed_at = datetime.now().isoformat()
        logger.error(f"Upload {job_id} error: {str(e)}")
        if job.retry_count < job.max_retries:
            job.status = UploadStatus.PENDING
            job.add_log(f"Retry scheduled (attempt {job.retry_count + 1}/{job.max_retries})")
            threading.Timer(10, start_upload_thread, args=[job_id]).start()

    finally:
        broadcast_progress(job_id)
        save_job_history(job)
