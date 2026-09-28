"""Routes package containing modular Flask blueprints."""
from .main import main_bp
from .auth import auth_bp
from .jobs import jobs_bp
from .channels import channels_bp
from .config import config_bp
from .supabase import supabase_bp
from .youtube import youtube_bp

__all__ = [
    'main_bp',
    'auth_bp',
    'jobs_bp',
    'channels_bp',
    'config_bp',
    'supabase_bp',
    'youtube_bp',
]
