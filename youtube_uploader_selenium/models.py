from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum
import json
import uuid
from datetime import datetime


class UploadStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SCHEDULED = "scheduled"


class UploadPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


@dataclass
class UploadJob:
    video_path: str
    metadata_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    profile_path: Optional[str] = None
    schedule: Optional[str] = None
    priority: str = "normal"
    job_id: str = ""
    status: UploadStatus = UploadStatus.PENDING
    progress: float = 0.0
    video_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    logs: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    channel_id: Optional[str] = None
    template_id: Optional[str] = None
    metadata: Optional[dict] = None

    def __post_init__(self):
        if not self.job_id:
            self.job_id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def add_log(self, message: str):
        from datetime import datetime
        self.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "video_path": self.video_path,
            "metadata_path": self.metadata_path,
            "thumbnail_path": self.thumbnail_path,
            "status": self.status.value,
            "progress": self.progress,
            "video_id": self.video_id,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "schedule": self.schedule,
            "priority": self.priority,
            "logs": self.logs[-20:],
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "channel_id": self.channel_id,
            "template_id": self.template_id,
            "metadata": self.metadata or {}
        }


class ChannelStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class AccountType(Enum):
    PERSONAL = "personal"
    BRAND = "brand"
    BUSINESS = "business"


@dataclass
class YouTubeChannel:
    channel_id: str = ""
    account_id: str = ""
    name: str = ""
    handle: str = ""
    description: str = ""
    status: ChannelStatus = ChannelStatus.ACTIVE
    account_type: AccountType = AccountType.PERSONAL
    is_managed: bool = False
    default_language: str = "en"
    country: str = "US"
    custom_url: Optional[str] = None
    subscriber_count: int = 0
    video_count: int = 0
    view_count: int = 0
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "channel_id": self.channel_id,
            "account_id": self.account_id,
            "name": self.name,
            "handle": self.handle,
            "description": self.description,
            "status": self.status.value,
            "account_type": self.account_type.value,
            "is_managed": self.is_managed,
            "default_language": self.default_language,
            "country": self.country,
            "custom_url": self.custom_url,
            "subscriber_count": self.subscriber_count,
            "video_count": self.video_count,
            "view_count": self.view_count,
            "created_at": self.created_at
        }


@dataclass
class YouTubeAccount:
    account_id: str = ""
    email: str = ""
    display_name: str = ""
    account_type: AccountType = AccountType.PERSONAL
    google_profile_image: Optional[str] = None
    is_verified: bool = False
    is_active: bool = True
    channels: List[str] = field(default_factory=list)
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    oauth_client_id: Optional[str] = None
    oauth_client_secret: Optional[str] = None
    created_at: str = ""
    last_login: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "account_id": self.account_id,
            "email": self.email,
            "display_name": self.display_name,
            "account_type": self.account_type.value,
            "google_profile_image": self.google_profile_image,
            "is_verified": self.is_verified,
            "is_active": self.is_active,
            "channels": self.channels,
            "created_at": self.created_at,
            "last_login": self.last_login
        }


@dataclass
class ChannelMetadataTemplate:
    template_id: str = ""
    channel_id: str = ""
    name: str = ""
    title_template: str = ""
    description_template: str = ""
    tags: List[str] = field(default_factory=list)
    category: str = "22"
    language: str = "en"
    privacy_status: str = "private"
    made_for_kids: bool = False
    upload_schedule: Optional[str] = None
    branding: dict = field(default_factory=dict)
    thumbnails: dict = field(default_factory=dict)
    created_at: str = ""
    is_default: bool = False

    def to_dict(self) -> dict:
        return {
            "template_id": self.template_id,
            "channel_id": self.channel_id,
            "name": self.name,
            "title_template": self.title_template,
            "description_template": self.description_template,
            "tags": self.tags,
            "category": self.category,
            "language": self.language,
            "privacy_status": self.privacy_status,
            "made_for_kids": self.made_for_kids,
            "upload_schedule": self.upload_schedule,
            "branding": self.branding,
            "thumbnails": self.thumbnails,
            "created_at": self.created_at,
            "is_default": self.is_default
        }

    def generate_title(self, video_title: str, **kwargs) -> str:
        result = self.title_template
        for key, value in kwargs.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        result = result.replace("{video_title}", video_title)
        return result

    def generate_description(self, video_description: str, **kwargs) -> str:
        result = self.description_template
        for key, value in kwargs.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        result = result.replace("{video_description}", video_description)
        return result


@dataclass
class BulkUploadBatch:
    batch_id: str = ""
    name: str = ""
    channel_id: str = ""
    account_id: str = ""
    video_paths: List[str] = field(default_factory=list)
    template_id: Optional[str] = None
    schedule: Optional[str] = None
    priority: str = "normal"
    status: str = "pending"
    total_videos: int = 0
    uploaded_count: int = 0
    failed_count: int = 0
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    def __post_init__(self):
        if not self.batch_id:
            import uuid
            self.batch_id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.total_videos = len(self.video_paths)

    def to_dict(self) -> dict:
        return {
            "batch_id": self.batch_id,
            "name": self.name,
            "channel_id": self.channel_id,
            "account_id": self.account_id,
            "video_paths": self.video_paths,
            "template_id": self.template_id,
            "schedule": self.schedule,
            "priority": self.priority,
            "status": self.status,
            "total_videos": self.total_videos,
            "uploaded_count": self.uploaded_count,
            "failed_count": self.failed_count,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }
