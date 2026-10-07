"""Socket.IO real-time event handlers."""
from flask import request, current_app
from flask_socketio import emit, join_room
from api.extensions import logger
from api.services.manager_service import (
    get_upload_queue,
    get_channel_manager,
    get_supabase,
)


def _extract_socket_token():
    """Pull the auth token from a Socket.IO connect request.

    Mirrors api/auth.py: bearer header, ?token= query param, or the
    `auth` payload dict sent by the socket.io client.
    """
    header = request.headers.get('Authorization', '')
    if header.startswith('Bearer '):
        return header[7:]
    return request.args.get('token') or request.args.get('auth_token')


def _authenticate_socket() -> bool:
    """Verify the socket client's token using the same rules as api/auth.py."""
    token = _extract_socket_token()
    if not token:
        return False
    supabase = get_supabase()
    user = supabase.verify_token(token)
    if user:
        return True
    # Local-dev fallbacks, same as require_auth.
    is_dev = current_app and (current_app.debug or current_app.config.get('ENV') == 'development')
    if is_dev and token.startswith('local-dev-jwt-'):
        return True
    if is_dev and token in ('dev-token', 'test-token', 'mock-token'):
        return True
    return False


def register_socket_events(socketio):
    """Register all Socket.IO real-time event handlers."""

    @socketio.on('connect')
    def handle_connect(auth=None):
        if isinstance(auth, dict) and auth.get('token') and not _extract_socket_token():
            # Client passed the token via the socket.io `auth` payload; honour it.
            token = auth.get('token')
            user = get_supabase().verify_token(token)
            if not user:
                is_dev = current_app and (current_app.debug or current_app.config.get('ENV') == 'development')
                if is_dev and (token.startswith('local-dev-jwt-') or token in ('dev-token', 'test-token', 'mock-token')):
                    user = {"id": "local-dev-user"}
            if not user:
                logger.warning('Socket connection rejected: unauthorized')
                return False
        elif not _authenticate_socket():
            logger.warning('Socket connection rejected: unauthorized')
            return False
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
        if job_id:
            # Scope the client to this job's room so progress is only pushed to subscribers.
            join_room(str(job_id))
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
