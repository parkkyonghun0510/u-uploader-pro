"""Application factory and package exports for YouTube Uploader API."""
from pathlib import Path
from flask import Flask
from dotenv import load_dotenv

from .config import CONFIG_MAP, ensure_directories
from .extensions import socketio, cors, logger, init_logging
from .routes import (
    main_bp,
    auth_bp,
    jobs_bp,
    channels_bp,
    config_bp,
    supabase_bp,
    youtube_bp,
)
from .sockets import register_socket_events

# Load environment variables on package initialization
load_dotenv()


def create_app(config_name: str = 'default') -> Flask:
    """Application factory for the YouTube Uploader Flask app."""
    project_root = Path(__file__).parent.parent

    app = Flask(
        __name__,
        template_folder=str(project_root / 'templates'),
        static_folder=str(project_root / 'static'),
    )

    # Apply configuration
    config_class = CONFIG_MAP.get(config_name, CONFIG_MAP['default'])
    app.config.from_object(config_class)

    # Ensure required runtime folders exist
    ensure_directories(app.config)

    # Initialize extensions and logging
    init_logging(app.config['LOGS_DIR'])
    cors.init_app(app)
    socketio.init_app(app)

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(channels_bp)
    app.register_blueprint(config_bp)
    app.register_blueprint(supabase_bp)
    app.register_blueprint(youtube_bp)

    # Register WebSocket events
    register_socket_events(socketio)

    return app


__all__ = ['create_app', 'socketio', 'logger']
