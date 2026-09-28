"""Socket.IO real-time event handlers."""
from flask_socketio import emit
from api.extensions import logger
from api.services.manager_service import (
    get_upload_queue,
    get_channel_manager,
    get_supabase,
)


def register_socket_events(socketio):
    """Register all Socket.IO real-time event handlers."""

    @socketio.on('connect')
    def handle_connect():
        supabase = get_supabase()
        logger.info('Client connected')
        emit('connection', {"status": "connected"})
        emit('supabase_status', {"connected": supabase.is_connected()})

    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info('Client disconnected')

    @socketio.on('request_jobs')
    def handle_request_jobs():
        queue = get_upload_queue()
        emit('jobs_update', [job.to_dict() for job in queue.get_all_jobs()])

    @socketio.on('request_channels')
    def handle_request_channels():
        cm = get_channel_manager()
        emit('channels_update', {
            "accounts": [acc.to_dict() for acc in cm.get_all_accounts()],
            "channels": [ch.to_dict() for ch in cm.get_all_channels()]
        })

    @socketio.on('request_analytics')
    def handle_request_analytics():
        cm = get_channel_manager()
        stats = cm.get_dashboard_stats()
        emit('analytics_update', stats)

    @socketio.on('subscribe_upload_progress')
    def handle_subscribe_progress(data):
        job_id = data.get('job_id')
        logger.info(f"Client subscribed to job {job_id} progress")
        emit('subscribed', {"job_id": job_id, "status": "active"})

    @socketio.on('request_supabase_sync')
    def handle_supabase_sync():
        supabase = get_supabase()
        if not supabase.is_connected():
            emit('sync_error', {"error": "Supabase not connected"})
            return
        try:
            accounts = [acc.to_dict() for acc in get_channel_manager().get_all_accounts()]
            channels = [ch.to_dict() for ch in get_channel_manager().get_all_channels()]
            jobs = [j.to_dict() for j in get_upload_queue().get_all_jobs()]
            emit('sync_complete', {"accounts": accounts, "channels": channels, "jobs": jobs})
        except Exception as e:
            emit('sync_error', {"error": str(e)})

    @socketio.on('request_notifications')
    def handle_request_notifications():
        supabase = get_supabase()
        if not supabase.is_connected():
            emit('notifications', [])
            return
        try:
            notifications = supabase.get_table('notifications').select('*').order(
                'created_at', desc=True
            ).execute()
            emit('notifications', notifications.data if notifications.data else [])
        except Exception:
            emit('notifications', [])
