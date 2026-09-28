"""YouTube Uploader Web Application Entrypoint.

This module exposes the Flask application instance, SocketIO server,
logger, and background services, maintaining full backwards-compatibility
while delegating modular logic to the api/ package.
"""
from api import create_app, socketio, logger
from api.auth import require_auth
from api.services.manager_service import (
    get_classes as _get_classes,
    get_config_manager,
    get_upload_queue,
    get_channel_manager,
    get_oauth_manager,
    get_google_oauth,
    get_supabase,
    get_supabase_client,
)
from api.services.uploader_service import (
    broadcast_progress,
    save_job_history,
    calculate_schedule_delay,
    start_upload_thread,
)

# Initialize application instance
app = create_app()

# Backward-compatible references
supabase = get_supabase()
supabase_client = get_supabase_client()


def start_web_app(host: str = '0.0.0.0', port: int = 8080, debug: bool = False):
    """Run the Flask-SocketIO server."""
    app.config['DEBUG'] = debug
    logger.info(f"Starting YouTube Uploader Dashboard on http://{host}:{port}")
    socketio.run(app, host=host, port=port, debug=debug, use_reloader=False, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    start_web_app()
