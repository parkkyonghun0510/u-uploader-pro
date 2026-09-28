import json
import time
import requests
from typing import Optional, List, Dict
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timedelta


class YouTubeAPI:
    def __init__(self, access_token: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.access_token = access_token
        self.api_key = api_key or self._load_api_key()
        self.session = requests.Session()
        if self.access_token:
            self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})

    def _load_api_key(self) -> Optional[str]:
        try:
            config_dir = Path("./config")
            api_key_file = config_dir / "youtube_api_key.txt"
            if api_key_file.exists():
                return api_key_file.read_text().strip()
        except:
            pass
        return None

    def save_api_key(self, api_key: str):
        config_dir = Path("./config")
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "youtube_api_key.txt").write_text(api_key)
        self.api_key = api_key

    def _make_request(self, endpoint: str, params: dict = None, method: str = "GET") -> Optional[dict]:
        url = f"{self.base_url}/{endpoint}"
        headers = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        if self.api_key:
            params = params or {}
            params["key"] = self.api_key
        try:
            response = self.session.request(method, url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                return {"error": "unauthorized", "message": "Access token expired or invalid"}
            if response.status_code == 403:
                return {"error": "quota_exceeded", "message": "YouTube API quota exceeded"}
            return {"error": str(e), "status": response.status_code}
        except Exception as e:
            return {"error": str(e)}

    # ---- Channels ----
    def get_my_channels(self) -> List[dict]:
        result = self._make_request("channels", {"part": "snippet,statistics,brandingSettings", "mine": "true"})
        if result and "items" in result:
            return result["items"]
        return []

    def get_channel_details(self, channel_id: str) -> Optional[dict]:
        result = self._make_request("channels", {
            "part": "snippet,statistics,contentDetails,brandingSettings",
            "id": channel_id
        })
        if result and "items" in result and result["items"]:
            return result["items"][0]
        return None

    def get_channel_videos(self, channel_id: str, max_results: int = 50) -> List[dict]:
        videos = []
        page_token = None
        while len(videos) < max_results:
            params = {
                "part": "snippet,statistics",
                "channelId": channel_id,
                "maxResults": min(50, max_results - len(videos)),
                "order": "date"
            }
            if page_token:
                params["pageToken"] = page_token
            result = self._make_request("search", params)
            if not result or "items" not in result:
                break
            items = result["items"]
            if not items:
                break
            videos.extend(items)
            page_token = result.get("nextPageToken")
            if not page_token:
                break
        return videos[:max_results]

    # ---- Video Upload ----
    def upload_video(self, video_path: str, title: str, description: str = "",
                      tags: list = None, category: str = "22", privacy: str = "private",
                      channel_id: Optional[str] = None) -> Optional[dict]:
        if not channel_id:
            channels = self.get_my_channels()
            if channels:
                channel_id = channels[0]["id"]
            else:
                return {"error": "no_channel", "message": "No YouTube channel found"}

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags or [],
                "categoryId": category
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False
            }
        }

        result = self._make_request("videos", {"part": "snippet,status"}, method="POST", params=body)
        return result

    def update_video_metadata(self, video_id: str, **kwargs) -> Optional[dict]:
        body = {"snippet": {}, "status": {}}
        for key, value in kwargs.items():
            if key in ["title", "description", "tags", "categoryId"]:
                body["snippet"][key] = value
            elif key in ["privacyStatus", "embeddable", "license"]:
                body["status"][key] = value
        result = self._make_request("videos", {"part": "snippet,status"}, method="PUT", params=body)
        return result

    def delete_video(self, video_id: str) -> bool:
        result = self._make_request("videos", {"id": video_id}, method="DELETE")
        return result is not None and "error" not in result

    # ---- Playlists ----
    def get_playlists(self, channel_id: str) -> List[dict]:
        result = self._make_request("playlists", {
            "part": "snippet,status",
            "channelId": channel_id,
            "maxResults": 50
        })
        if result and "items" in result:
            return result["items"]
        return []

    def create_playlist(self, channel_id: str, title: str, description: str = "") -> Optional[dict]:
        body = {
            "snippet": {"title": title, "description": description},
            "status": {"privacyStatus": "private"}
        }
        result = self._make_request("playlists", {"part": "snippet,status"}, method="POST", params=body)
        return result

    # ---- Analytics ----
    def get_channel_analytics(self, channel_id: str, date: str = None) -> Optional[dict]:
        end_date = date or datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        result = self._make_request("reports", {
            "part": "statistics",
            "ids": f"channel=={channel_id}",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": "views,likes,dislikes,comments,subscribers",
            "dimensions": "day"
        })
        return result

    def get_video_analytics(self, video_id: str) -> Optional[dict]:
        result = self._make_request("videos", {
            "part": "statistics,snippet,status",
            "id": video_id
        })
        if result and "items" in result and result["items"]:
            return result["items"][0]
        return None

    # ---- Search ----
    def search_videos(self, query: str, max_results: int = 10) -> List[dict]:
        result = self._make_request("search", {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max_results
        })
        if result and "items" in result:
            return result["items"]
        return []

    def search_channels(self, query: str) -> List[dict]:
        result = self._make_request("search", {
            "part": "snippet",
            "q": query,
            "type": "channel",
            "maxResults": 10
        })
        if result and "items" in result:
            return result["items"]
        return []


@dataclass
class UploadSchedule:
    channel_id: str
    template_id: str
    video_path: str
    scheduled_time: str
    metadata: dict = None
    status: str = "pending"

    def to_dict(self) -> dict:
        return {
            "channel_id": self.channel_id,
            "template_id": self.template_id,
            "video_path": self.video_path,
            "scheduled_time": self.scheduled_time,
            "metadata": self.metadata or {},
            "status": self.status
        }
