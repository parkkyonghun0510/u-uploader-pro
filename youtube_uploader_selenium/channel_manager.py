import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, List

from youtube_uploader_selenium.models import YouTubeAccount, YouTubeChannel, ChannelMetadataTemplate, BulkUploadBatch, AccountType


class ChannelManager:
    def __init__(self, config_dir: str = "./config"):
        self.config_dir = Path(config_dir)
        self.accounts_file = self.config_dir / "accounts.json"
        self.channels_file = self.config_dir / "channels.json"
        self.templates_file = self.config_dir / "templates.json"
        self.batches_file = self.config_dir / "batches.json"
        self._accounts: dict = {}
        self._channels: dict = {}
        self._templates: dict = {}
        self._batches: dict = {}
        self._load_all()

    def _load_all(self):
        if self.accounts_file.exists():
            try:
                with open(self.accounts_file) as f:
                    data = json.load(f)
                    for aid, acc_data in data.items():
                        acc = YouTubeAccount(account_id=aid, **acc_data)
                        self._accounts[aid] = acc
            except:
                pass
        if self.channels_file.exists():
            try:
                with open(self.channels_file) as f:
                    data = json.load(f)
                    for cid, ch_data in data.items():
                        ch = YouTubeChannel(channel_id=cid, **ch_data)
                        self._channels[cid] = ch
            except:
                pass
        if self.templates_file.exists():
            try:
                with open(self.templates_file) as f:
                    data = json.load(f)
                    for tid, temp_data in data.items():
                        temp = ChannelMetadataTemplate(template_id=tid, **temp_data)
                        self._templates[tid] = temp
            except:
                pass
        if self.batches_file.exists():
            try:
                with open(self.batches_file) as f:
                    data = json.load(f)
                    for bid, batch_data in data.items():
                        batch = BulkUploadBatch(batch_id=bid, **batch_data)
                        self._batches[bid] = batch
            except:
                pass

    def _save_accounts(self):
        data = {aid: acc.to_dict() for aid, acc in self._accounts.items()}
        with open(self.accounts_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _save_channels(self):
        data = {cid: ch.to_dict() for cid, ch in self._channels.items()}
        with open(self.channels_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _save_templates(self):
        data = {tid: temp.to_dict() for tid, temp in self._templates.items()}
        with open(self.templates_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _save_batches(self):
        data = {bid: batch.to_dict() for bid, batch in self._batches.items()}
        with open(self.batches_file, 'w') as f:
            json.dump(data, f, indent=2)

    # ---- Accounts ----
    def add_account(self, email: str, display_name: str, account_type: str = "personal",
                    access_token: Optional[str] = None, refresh_token: Optional[str] = None) -> YouTubeAccount:
        account_id = str(uuid.uuid4())
        account = YouTubeAccount(
            account_id=account_id,
            email=email,
            display_name=display_name,
            account_type=AccountType(account_type),
            access_token=access_token,
            refresh_token=refresh_token,
            created_at=datetime.now().isoformat()
        )
        self._accounts[account_id] = account
        self._save_accounts()
        return account

    def remove_account(self, account_id: str):
        if account_id in self._accounts:
            del self._accounts[account_id]
            self._save_accounts()
            for cid in list(self._channels.keys()):
                if self._channels[cid].account_id == account_id:
                    del self._channels[cid]
            self._save_channels()

    def get_account(self, account_id: str) -> Optional[YouTubeAccount]:
        return self._accounts.get(account_id)

    def get_all_accounts(self) -> List[YouTubeAccount]:
        return list(self._accounts.values())

    def update_account(self, account_id: str, **kwargs) -> Optional[YouTubeAccount]:
        account = self._accounts.get(account_id)
        if not account:
            return None
        for key, value in kwargs.items():
            if hasattr(account, key):
                if key == 'account_type' and isinstance(value, str):
                    value = AccountType(value)
                setattr(account, key, value)
        self._save_accounts()
        return account

    def set_active_account(self, account_id: str):
        self._active_account_id = account_id

    def get_active_account(self) -> Optional[YouTubeAccount]:
        return self._accounts.get(getattr(self, '_active_account_id', None))

    # ---- Channels ----
    def add_channel(self, account_id: str, channel_id: str, name: str, handle: str = "",
                    description: str = "", is_managed: bool = False) -> YouTubeChannel:
        channel = YouTubeChannel(
            channel_id=channel_id,
            account_id=account_id,
            name=name,
            handle=handle,
            description=description,
            is_managed=is_managed,
            created_at=datetime.now().isoformat()
        )
        self._channels[channel_id] = channel
        if account_id in self._accounts:
            if channel_id not in self._accounts[account_id].channels:
                self._accounts[account_id].channels.append(channel_id)
                self._save_accounts()
        self._save_channels()
        return channel

    def remove_channel(self, channel_id: str):
        if channel_id in self._channels:
            del self._channels[channel_id]
            self._save_channels()

    def get_channel(self, channel_id: str) -> Optional[YouTubeChannel]:
        return self._channels.get(channel_id)

    def get_channels_by_account(self, account_id: str) -> List[YouTubeChannel]:
        return [ch for ch in self._channels.values() if ch.account_id == account_id]

    def get_all_channels(self) -> List[YouTubeChannel]:
        return list(self._channels.values())

    def update_channel(self, channel_id: str, **kwargs) -> Optional[YouTubeChannel]:
        channel = self._channels.get(channel_id)
        if not channel:
            return None
        for key, value in kwargs.items():
            if hasattr(channel, key):
                if key == 'status' and isinstance(value, str):
                    from youtube_uploader_selenium.models import ChannelStatus
                    value = ChannelStatus(value)
                setattr(channel, key, value)
        self._save_channels()
        return channel

    def get_active_channel(self) -> Optional[YouTubeChannel]:
        active_account = self.get_active_account()
        if active_account and active_account.channels:
            return self._channels.get(active_account.channels[0])
        if self._channels:
            return list(self._channels.values())[0]
        return None

    # ---- Metadata Templates ----
    def add_template(self, channel_id: str, name: str, title_template: str = "",
                     description_template: str = "", tags: list = None, **kwargs) -> ChannelMetadataTemplate:
        template_id = str(uuid.uuid4())
        template = ChannelMetadataTemplate(
            template_id=template_id,
            channel_id=channel_id,
            name=name,
            title_template=title_template,
            description_template=description_template,
            tags=tags or [],
            created_at=datetime.now().isoformat(),
            **kwargs
        )
        self._templates[template_id] = template
        self._save_templates()
        return template

    def get_templates_by_channel(self, channel_id: str) -> List[ChannelMetadataTemplate]:
        return [t for t in self._templates.values() if t.channel_id == channel_id]

    def get_all_templates(self) -> List[ChannelMetadataTemplate]:
        return list(self._templates.values())

    def get_default_template(self, channel_id: str) -> Optional[ChannelMetadataTemplate]:
        for t in self._templates.values():
            if t.channel_id == channel_id and t.is_default:
                return t
        templates = [t for t in self._templates.values() if t.channel_id == channel_id]
        return templates[0] if templates else None

    # ---- Bulk Upload Batches ----
    def create_batch(self, channel_id: str, account_id: str, name: str,
                     video_paths: list, template_id: Optional[str] = None,
                     schedule: Optional[str] = None, priority: str = "normal") -> BulkUploadBatch:
        batch = BulkUploadBatch(
            batch_id=str(uuid.uuid4()),
            name=name,
            channel_id=channel_id,
            account_id=account_id,
            video_paths=video_paths,
            template_id=template_id,
            schedule=schedule,
            priority=priority,
            created_at=datetime.now().isoformat()
        )
        self._batches[batch.batch_id] = batch
        self._save_batches()
        return batch

    def get_batch(self, batch_id: str) -> Optional[BulkUploadBatch]:
        return self._batches.get(batch_id)

    def get_all_batches(self) -> List[BulkUploadBatch]:
        return list(self._batches.values())

    def update_batch_status(self, batch_id: str, status: str, uploaded: int = 0, failed: int = 0):
        batch = self._batches.get(batch_id)
        if batch:
            batch.status = status
            batch.uploaded_count = uploaded
            batch.failed_count = failed
            self._save_batches()

    # ---- Dashboard Stats ----
    def get_dashboard_stats(self) -> dict:
        all_channels = self.get_all_channels()
        all_accounts = self.get_all_accounts()
        all_jobs_from_queue = []
        try:
            from youtube_uploader_selenium.queue import UploadQueue
            queue = UploadQueue()
            all_jobs_from_queue = list(queue.jobs.values()) if hasattr(queue, 'jobs') else []
        except:
            pass
        total_uploads = len(all_jobs_from_queue)
        completed = sum(1 for j in all_jobs_from_queue if getattr(j, 'status', None) == 'completed')
        failed = sum(1 for j in all_jobs_from_queue if getattr(j, 'status', None) == 'failed')
        return {
            "total_accounts": len(all_accounts),
            "total_channels": len(all_channels),
            "total_templates": len(self._templates),
            "total_batches": len(self._batches),
            "total_uploads": total_uploads,
            "completed_uploads": completed,
            "failed_uploads": failed,
            "active_channels": sum(1 for ch in all_channels if ch.status.value == 'active'),
            "channels_per_account": {acc.display_name: len(self.get_channels_by_account(acc.account_id)) for acc in all_accounts}
        }

    def get_channel_analytics(self, channel_id: str) -> dict:
        channel = self._channels.get(channel_id)
        if not channel:
            return {}
        channel_jobs = []
        try:
            from youtube_uploader_selenium.queue import UploadQueue
            queue = UploadQueue()
            jobs = list(queue.jobs.values()) if hasattr(queue, 'jobs') else []
            channel_jobs = [j for j in jobs if getattr(j, 'channel_id', None) == channel_id]
        except:
            pass
        return {
            "channel_id": channel_id,
            "channel_name": channel.name,
            "subscriber_count": channel.subscriber_count,
            "total_videos_uploaded": len(channel_jobs),
            "completed": sum(1 for j in channel_jobs if getattr(j, 'status', None) == 'completed'),
            "failed": sum(1 for j in channel_jobs if getattr(j, 'status', None) == 'failed'),
            "in_progress": sum(1 for j in channel_jobs if getattr(j, 'status', None) == 'in_progress'),
            "average_upload_time": "0m",
            "last_upload": max([getattr(j, 'completed_at', '') for j in channel_jobs], default=None)
        }
