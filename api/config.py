"""Configuration classes for Flask YouTube Uploader application."""
import os
from pathlib import Path


class Config:
    """Base application configuration."""
    ROOT_DIR = Path.cwd()
    SECRET_KEY = os.environ.get('SECRET_KEY', 'youtube-uploader-secret-key-change-me')
    UPLOAD_FOLDER = str(ROOT_DIR)
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024 * 1024  # 10 GB
    LOGS_DIR = str(ROOT_DIR / 'logs')
    CONFIG_DIR = str(ROOT_DIR / 'config')
    QUEUE_DIR = str(ROOT_DIR / 'queue')

    SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://aisbzppswxqknjvntaaa.supabase.co')
    SUPABASE_ANON_KEY = os.environ.get(
        'SUPABASE_ANON_KEY',
        'sb_publishable__LERUIuVlqzUksHA3-AU3g_GSW-YxoE'
    )
    SUPABASE_SERVICE_ROLE_KEY = os.environ.get(
        'SUPABASE_SERVICE_ROLE_KEY',
        ''
    )


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True


CONFIG_MAP = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}


def ensure_directories(config_obj):
    """Ensure required application directories exist."""
    os.makedirs(config_obj.get('LOGS_DIR', Config.LOGS_DIR), exist_ok=True)
    os.makedirs(config_obj.get('CONFIG_DIR', Config.CONFIG_DIR), exist_ok=True)
    os.makedirs(config_obj.get('QUEUE_DIR', Config.QUEUE_DIR), exist_ok=True)
