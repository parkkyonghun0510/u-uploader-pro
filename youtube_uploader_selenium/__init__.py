from youtube_uploader_selenium.models import UploadJob, UploadStatus, UploadPriority, YouTubeAccount, YouTubeChannel, ChannelMetadataTemplate, BulkUploadBatch
from youtube_uploader_selenium.config import ConfigManager
from youtube_uploader_selenium.queue import UploadQueue
from youtube_uploader_selenium.channel_manager import ChannelManager
from youtube_uploader_selenium.youtube_api import YouTubeAPI, UploadSchedule
from youtube_uploader_selenium.oauth import GoogleOAuth2, OAuthManager
from youtube_uploader_selenium.legacy_uploader import YouTubeUploader, load_metadata
from youtube_uploader_selenium.utils import get_video_duration, format_file_size
import os
import platform
import logging

logger = logging.getLogger(__name__)

class YouTubeUploaderSession:
    def __init__(self, video_path, metadata_json_path=None, thumbnail_path=None, profile_path=None, job_id=None):
        self.video_path = video_path
        self.thumbnail_path = thumbnail_path
        self.metadata_dict = load_metadata(metadata_json_path)
        self.job_id = job_id
        self.profile_path = profile_path or str(os.path.curdir) + "/profile"
        self.logger = logging.getLogger(f"YouTubeUploader-{job_id or 'main'}")
        self.is_mac = not any(os_name in platform.platform() for os_name in ["Windows", "Linux"])
        self._validate_inputs()
        self.uploader = YouTubeUploader(video_path, metadata_json_path, thumbnail_path, self.profile_path)

    def _validate_inputs(self):
        if not self.metadata_dict.get('title'):
            self.metadata_dict['title'] = os.path.splitext(os.path.basename(self.video_path))[0]

    def upload_with_progress(self, progress_callback=None):
        try:
            result = self.uploader.upload()
            if progress_callback:
                progress_callback(100.0)
            return result
        except Exception as e:
            if progress_callback:
                progress_callback(-1)
            raise
        finally:
            try:
                self.uploader.__quit()
            except:
                pass
