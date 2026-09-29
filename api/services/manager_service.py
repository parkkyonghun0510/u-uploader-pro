"""Manager singletons and service registry."""
from pathlib import Path
from flask import current_app
from youtube_uploader_selenium.supabase_manager import SupabaseManager


def get_classes():
    """Lazy-load and return core domain classes."""
    from youtube_uploader_selenium import YouTubeUploader
    from youtube_uploader_selenium.models import (
        UploadJob, UploadStatus, UploadPriority,
        YouTubeAccount, YouTubeChannel, ChannelMetadataTemplate, BulkUploadBatch
    )
    from youtube_uploader_selenium.config import ConfigManager
    from youtube_uploader_selenium.queue import UploadQueue
    from youtube_uploader_selenium.channel_manager import ChannelManager
    from youtube_uploader_selenium.youtube_api import YouTubeAPI
    from youtube_uploader_selenium.oauth import GoogleOAuth2, OAuthManager

    return (
        YouTubeUploader, UploadJob, UploadStatus, UploadPriority,
        ConfigManager, UploadQueue, ChannelManager, YouTubeAPI,
        GoogleOAuth2, OAuthManager, YouTubeAccount, YouTubeChannel,
        ChannelMetadataTemplate, BulkUploadBatch
    )


def _get_config_dir(custom_dir: str = None) -> str:
    """Resolve config directory path."""
    if custom_dir:
        return custom_dir
    try:
        if current_app and 'CONFIG_DIR' in current_app.config:
            return current_app.config['CONFIG_DIR']
    except RuntimeError:
        pass
    return str(Path.cwd() / 'config')


def get_config_manager(config_dir: str = None):
    """Retrieve singleton ConfigManager instance."""
    if not hasattr(get_config_manager, '_instance'):
        _, _, _, _, ConfigManager, _, _, _, _, _, _, _, _, _ = get_classes()
        get_config_manager._instance = ConfigManager(_get_config_dir(config_dir))
    return get_config_manager._instance


def get_upload_queue():
    """Retrieve singleton UploadQueue instance."""
    if not hasattr(get_upload_queue, '_instance'):
        _, _, _, _, _, UploadQueue, _, _, _, _, _, _, _, _ = get_classes()
        get_upload_queue._instance = UploadQueue()
    return get_upload_queue._instance


def get_channel_manager(config_dir: str = None):
    """Retrieve singleton ChannelManager instance."""
    if not hasattr(get_channel_manager, '_instance'):
        _, _, _, _, _, _, ChannelManager, _, _, _, _, _, _, _ = get_classes()
        get_channel_manager._instance = ChannelManager(_get_config_dir(config_dir))
    return get_channel_manager._instance


def get_oauth_manager(config_dir: str = None):
    """Retrieve singleton OAuthManager instance."""
    if not hasattr(get_oauth_manager, '_instance'):
        _, _, _, _, _, _, _, _, _, OAuthManager, _, _, _, _ = get_classes()
        get_oauth_manager._instance = OAuthManager(_get_config_dir(config_dir))
    return get_oauth_manager._instance


def get_google_oauth(config_dir: str = None):
    """Retrieve singleton GoogleOAuth2 instance."""
    if not hasattr(get_google_oauth, '_instance'):
        _, _, _, _, _, _, _, _, GoogleOAuth2, _, _, _, _, _ = get_classes()
        get_google_oauth._instance = GoogleOAuth2(_get_config_dir(config_dir))
    return get_google_oauth._instance


def reset_managers():
    """Reset singleton manager instances for test isolation."""
    for fn in (get_config_manager, get_upload_queue, get_channel_manager, get_oauth_manager, get_google_oauth):
        if hasattr(fn, '_instance'):
            delattr(fn, '_instance')


def get_supabase():
    """Retrieve SupabaseManager singleton instance."""
    return SupabaseManager.get_instance()


def get_supabase_client():
    """Retrieve Supabase client if connected."""
    sm = get_supabase()
    return sm.client if sm.is_connected() else None
