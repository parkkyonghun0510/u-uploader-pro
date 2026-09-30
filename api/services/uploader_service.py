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
    get_supabase,
    get_supabase_client,
    get_oauth_manager,
    get_google_oauth,
    get_channel_manager,
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
        try:
            socketio.emit('upload_progress', job.to_dict())
        except Exception as e:
            logger.debug(f"SocketIO broadcast notice: {e}")
        try:
            client = get_supabase_client()
            if client:
                threading.Thread(target=_sync_job_to_supabase, args=[job], daemon=True).start()
        except Exception as e:
            logger.debug(f"Supabase sync dispatch error: {e}")


def _sync_job_to_supabase(job):
    """Sync upload job to Supabase in background."""
    try:
        sm = get_supabase()
        if sm.is_connected() and sm.client:
            sm.client.table('upload_jobs').update({
                'status': job.status.value,
                'progress': job.progress,
                'video_id': getattr(job, 'video_id', None),
                'error_message': getattr(job, 'error_message', None),
                'completed_at': job.completed_at,
            }).eq('id', str(job.job_id)).execute()
    except Exception as e:
        logger.debug(f"Supabase sync notice: {e}")


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

    try:
        sm = get_supabase()
        if sm.is_connected() and sm.client:
            threading.Thread(target=_sync_history_to_supabase, args=[job], daemon=True).start()
    except Exception as e:
        logger.debug(f"Supabase history dispatch notice: {e}")


def _sync_history_to_supabase(job):
    """Sync upload history record to Supabase."""
    try:
        sm = get_supabase()
        if sm.is_connected() and sm.client:
            sm.client.table('upload_history').insert({
                'job_id': str(job.job_id),
                'channel_id': str(job.channel_id) if job.channel_id else None,
                'video_id': getattr(job, 'video_id', None),
                'video_title': getattr(job, 'video_title', None),
                'status': job.status.value,
                'progress': job.progress,
                'duration_seconds': getattr(job, 'duration_seconds', None),
                'file_size': getattr(job, 'file_size', None),
                'error_message': getattr(job, 'error_message', None),
            }).execute()
    except Exception as e:
        logger.debug(f"History sync notice: {e}")


def calculate_schedule_delay(schedule_str: str) -> float:
    """Calculate delay seconds until scheduled upload time."""
    try:
        sched_time = datetime.strptime(schedule_str, "%m/%d/%Y, %H:%M")
        now = datetime.now()
        delay = (sched_time - now).total_seconds()
        return max(delay, 1)
    except Exception:
        return 1.0


def _execute_api_upload(job, access_token: str):
    """Execute video upload via YouTube Data API v3 resumable chunk upload."""
    _, _, UploadStatus, _, _, _, _, YouTubeAPI, _, _, _, _, _, _ = get_classes()
    api = YouTubeAPI(access_token=access_token)

    title = None
    description = ""
    tags = []
    privacy = "public"
    category = "22"

    # 1. Load from metadata file if present
    if job.metadata_path and Path(job.metadata_path).exists():
        try:
            with open(job.metadata_path, 'r', encoding='utf-8') as f:
                file_meta = json.load(f)
                if isinstance(file_meta, dict):
                    title = file_meta.get('title')
                    description = file_meta.get('description', '')
                    tags = file_meta.get('tags', [])
                    privacy = file_meta.get('privacy', file_meta.get('privacyStatus', 'public'))
                    category = str(file_meta.get('category', file_meta.get('categoryId', '22')))
        except Exception as e:
            job.add_log(f"Warning: could not read metadata_path: {e}")

    # 2. Override from job.metadata dict if present
    job_meta = getattr(job, 'metadata', None)
    if isinstance(job_meta, dict) and job_meta:
        if job_meta.get('title'):
            title = job_meta['title']
        if 'description' in job_meta:
            description = job_meta['description']
        if 'tags' in job_meta:
            tags = job_meta['tags']
        if job_meta.get('privacy'):
            privacy = job_meta['privacy']
        if job_meta.get('category'):
            category = str(job_meta['category'])

    # Fallback to filename stem
    if not title:
        title = Path(job.video_path).stem

    job.add_log(f"Uploading via YouTube Data API v3: '{title}' [{privacy}]")
    logger.info(f"Job {job.job_id}: starting YouTube Data API v3 upload: {title}")

    def progress_callback(pct: float):
        job.progress = pct
        broadcast_progress(job.job_id)

    success, video_id, err = api.upload_video_resumable(
        video_path=job.video_path,
        title=title,
        description=description,
        tags=tags,
        category=category,
        privacy=privacy,
        thumbnail_path=job.thumbnail_path,
        progress_callback=progress_callback
    )

    if success:
        job.status = UploadStatus.COMPLETED
        job.video_id = video_id
        job.progress = 100.0
        job.completed_at = datetime.now().isoformat()
        job.add_log(f"Upload completed successfully via YouTube Data API v3! Video ID: {video_id}")
        logger.info(f"Upload {job.job_id} completed successfully via API. Video ID: {video_id}")
    else:
        # Check if fallback to Selenium is viable
        profiles_dir = Path("./profiles")
        default_dir = Path("./profile")
        has_selenium_profile = bool(
            job.profile_path or
            default_dir.exists() or
            (profiles_dir.exists() and any(p.is_dir() for p in profiles_dir.iterdir()))
        )
        if has_selenium_profile:
            job.add_log(f"YouTube Data API upload unavailable ({err}). Automatically falling back to browser automation (Selenium)...")
            logger.warning(f"Job {job.job_id}: API upload failed ({err}). Falling back to Selenium.")
            _execute_selenium_upload(job)
            return

        job.status = UploadStatus.FAILED
        job.error_message = err or "Upload failed via YouTube API"
        job.completed_at = datetime.now().isoformat()
        job.add_log(f"API Upload failed: {job.error_message}")
        logger.error(f"Upload {job.job_id} failed via API: {job.error_message}")


def _execute_selenium_upload(job):
    """Execute legacy Selenium Firefox upload."""
    YouTubeUploader, _, UploadStatus, _, _, _, _, _, _, _, _, _, _, _ = get_classes()
    uploader = YouTubeUploader(
        video_path=job.video_path,
        metadata_json_path=job.metadata_path,
        thumbnail_path=job.thumbnail_path,
        profile_path=job.profile_path,
    )

    job.add_log(f"Starting upload via Selenium for {job.video_path}")
    if job.channel_id:
        job.add_log(f"Target channel: {job.channel_id}")
    was_uploaded, video_id = uploader.upload()

    if was_uploaded:
        job.status = UploadStatus.COMPLETED
        job.video_id = video_id
        job.progress = 100.0
        job.completed_at = datetime.now().isoformat()
        job.add_log(f"Upload completed! Video ID: {video_id}")
        logger.info(f"Upload {job.job_id} completed successfully via Selenium")
    else:
        job.status = UploadStatus.FAILED
        job.error_message = "Upload was cancelled or failed via Selenium"
        job.completed_at = datetime.now().isoformat()
        logger.warning(f"Upload {job.job_id} failed via Selenium")


def _update_batch_progress(job):
    """If this job belongs to a bulk upload batch, update batch statistics in ChannelManager."""
    try:
        batch_id = (job.metadata or {}).get("batch_id")
        if not batch_id:
            return
        channel_manager = get_channel_manager()
        batch = channel_manager.get_batch(batch_id)
        if not batch:
            return
        _, _, UploadStatus, _, _, _, _, _, _, _, _, _, _, _ = get_classes()
        if job.status == UploadStatus.COMPLETED:
            batch.uploaded_count = (batch.uploaded_count or 0) + 1
        elif job.status == UploadStatus.FAILED and (job.retry_count >= job.max_retries or not job.max_retries):
            batch.failed_count = (batch.failed_count or 0) + 1

        total = batch.total_videos or 1
        if (batch.uploaded_count + batch.failed_count) >= total:
            batch.status = "completed" if (batch.failed_count or 0) == 0 else "completed_with_errors"
            batch.completed_at = datetime.now().isoformat()
        else:
            batch.status = "running"
            if not batch.started_at:
                batch.started_at = datetime.now().isoformat()
        channel_manager._save_batches()
    except Exception as e:
        logger.warning(f"Failed to update batch progress for job {job.job_id}: {e}")


def start_upload_thread(job_id: str):
    """Background worker thread to run YouTube upload via YouTube Data API v3 or Selenium."""
    queue = get_upload_queue()
    job = queue.get_job(job_id)
    if not job:
        return

    try:
        _, _, UploadStatus, _, _, _, _, _, _, _, _, _, _, _ = get_classes()
        job.status = UploadStatus.IN_PROGRESS
        job.started_at = datetime.now().isoformat()
        job.progress = 0.0
        broadcast_progress(job_id)

        oauth_mgr = get_oauth_manager()
        google_oauth = get_google_oauth()

        access_token = oauth_mgr.get_valid_access_token(
            account_id=job.channel_id,
            channel_id=job.channel_id,
            google_oauth=google_oauth
        )

        if access_token:
            _execute_api_upload(job, access_token)
        else:
            job.add_log("No active OAuth token found, falling back to Selenium browser uploader")
            _execute_selenium_upload(job)

    except Exception as e:
        _, _, UploadStatus, _, _, _, _, _, _, _, _, _, _, _ = get_classes()
        job.status = UploadStatus.FAILED
        job.error_message = str(e)
        job.completed_at = datetime.now().isoformat()
        logger.error(f"Upload {job_id} error: {str(e)}")
        if job.retry_count < job.max_retries:
            job.retry_count += 1
            job.status = UploadStatus.PENDING
            job.add_log(f"Retry scheduled (attempt {job.retry_count}/{job.max_retries})")
            threading.Timer(10, start_upload_thread, args=[job_id]).start()

    finally:
        _update_batch_progress(job)
        broadcast_progress(job_id)
        save_job_history(job)


