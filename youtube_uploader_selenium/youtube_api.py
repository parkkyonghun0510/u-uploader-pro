import json
import time
import os
import requests
from typing import Optional, List, Dict, Tuple
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
        env_key = os.environ.get("YOUTUBE_API_KEY", "").strip() or os.environ.get("GOOGLE_API_KEY", "").strip()
        if env_key:
            return env_key
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
        result = self._make_request("channels", {
            "part": "snippet,statistics,contentDetails,brandingSettings,status",
            "mine": "true"
        })
        if result and "items" in result:
            return result["items"]
        return []

    def get_channel_details(self, channel_id: str) -> Optional[dict]:
        result = self._make_request("channels", {
            "part": "snippet,statistics,contentDetails,brandingSettings,status",
            "id": channel_id
        })
        if result and "items" in result and result["items"]:
            return result["items"][0]
        return None

    def get_channel_videos(self, channel_id: str, max_results: int = 50) -> List[dict]:
        """
        Fetch recent videos for a channel.
        First attempts to read from channel's uploads playlist (1 quota unit)
        with full video statistics, falling back to search if needed.
        """
        videos = []
        uploads_playlist_id = None
        if channel_id and channel_id.startswith("UC") and len(channel_id) > 2:
            uploads_playlist_id = "UU" + channel_id[2:]

        # Method 1: Low-quota playlistItems from uploads playlist
        if uploads_playlist_id:
            try:
                res = self._make_request("playlistItems", {
                    "part": "snippet,contentDetails,status",
                    "playlistId": uploads_playlist_id,
                    "maxResults": min(50, max_results)
                })
                if res and "items" in res and res["items"]:
                    items = res["items"]
                    video_ids = [item.get("contentDetails", {}).get("videoId") for item in items if item.get("contentDetails", {}).get("videoId")]
                    
                    # Fetch rich statistics in batch
                    stats_map = {}
                    if video_ids:
                        v_res = self._make_request("videos", {
                            "part": "snippet,statistics,status,contentDetails",
                            "id": ",".join(video_ids[:50])
                        })
                        if v_res and "items" in v_res:
                            for v in v_res["items"]:
                                stats_map[v.get("id")] = v

                    for item in items:
                        vid = item.get("contentDetails", {}).get("videoId")
                        full_v = stats_map.get(vid, {})
                        snippet = full_v.get("snippet") or item.get("snippet", {})
                        v_stats = full_v.get("statistics", {})
                        v_status = full_v.get("status") or item.get("status", {})
                        
                        try:
                            v_views = int(v_stats.get("viewCount", 0))
                        except (ValueError, TypeError):
                            v_views = 0
                        try:
                            v_likes = int(v_stats.get("likeCount", 0))
                        except (ValueError, TypeError):
                            v_likes = 0
                        try:
                            v_comments = int(v_stats.get("commentCount", 0))
                        except (ValueError, TypeError):
                            v_comments = 0

                        videos.append({
                            "id": {"videoId": vid} if vid else item.get("id"),
                            "videoId": vid,
                            "snippet": snippet,
                            "statistics": v_stats,
                            "status": v_status,
                            "view_count": v_views,
                            "like_count": v_likes,
                            "comment_count": v_comments,
                            "privacy_status": v_status.get("privacyStatus", "public"),
                            "watch_url": f"https://www.youtube.com/watch?v={vid}" if vid else "",
                            "studio_url": f"https://studio.youtube.com/video/{vid}/edit" if vid else ""
                        })
                    if videos:
                        return videos[:max_results]
            except Exception:
                pass

        # Method 2: Fallback to search endpoint
        page_token = None
        while len(videos) < max_results:
            params = {
                "part": "snippet",
                "channelId": channel_id,
                "maxResults": min(50, max_results - len(videos)),
                "order": "date",
                "type": "video"
            }
            if page_token:
                params["pageToken"] = page_token
            result = self._make_request("search", params)
            if not result or "items" not in result:
                break
            items = result["items"]
            if not items:
                break
            for it in items:
                vid = it.get("id", {}).get("videoId") if isinstance(it.get("id"), dict) else it.get("id")
                it["videoId"] = vid
                it["watch_url"] = f"https://www.youtube.com/watch?v={vid}" if vid else ""
                it["studio_url"] = f"https://studio.youtube.com/video/{vid}/edit" if vid else ""
                videos.append(it)
            page_token = result.get("nextPageToken")
            if not page_token:
                break
        return videos[:max_results]

    def get_studio_dashboard(self, channel_id: Optional[str] = None) -> dict:
        """
        Fetch comprehensive YouTube Studio data package for creator dashboard.
        Includes channel branding, metrics, and recent video analytics.
        """
        channel_data = None
        if channel_id:
            channel_data = self.get_channel_details(channel_id)
        if not channel_data:
            channels = self.get_my_channels()
            if channels:
                channel_data = channels[0]

        if not channel_data or not isinstance(channel_data, dict):
            return {
                "error": "channel_not_found",
                "message": "No YouTube channel could be found for this token or channel ID."
            }

        cid = channel_data.get("id", channel_id or "")
        snippet = channel_data.get("snippet", {})
        stats = channel_data.get("statistics", {})
        branding = channel_data.get("brandingSettings", {})
        content_details = channel_data.get("contentDetails", {})

        banner = (
            branding.get("image", {}).get("bannerExternalUrl") or
            branding.get("channel", {}).get("featuredImageUrl", "")
        )
        thumbs = snippet.get("thumbnails", {})
        avatar = (
            thumbs.get("high", {}).get("url") or
            thumbs.get("medium", {}).get("url") or
            thumbs.get("default", {}).get("url") or ""
        )

        try:
            subs = int(stats.get("subscriberCount", 0))
        except (ValueError, TypeError):
            subs = 0
        try:
            vids = int(stats.get("videoCount", 0))
        except (ValueError, TypeError):
            vids = 0
        try:
            views = int(stats.get("viewCount", 0))
        except (ValueError, TypeError):
            views = 0

        recent_videos = self.get_channel_videos(cid, max_results=12)

        return {
            "channel": {
                "id": cid,
                "title": snippet.get("title", ""),
                "handle": snippet.get("customUrl", ""),
                "description": snippet.get("description", ""),
                "published_at": snippet.get("publishedAt", ""),
                "country": snippet.get("country", ""),
                "default_language": snippet.get("defaultLanguage", "en"),
                "avatar_url": avatar,
                "banner_url": banner,
                "subscriber_count": subs,
                "video_count": vids,
                "view_count": views,
                "hidden_subscriber_count": stats.get("hiddenSubscriberCount", False),
                "uploads_playlist_id": content_details.get("relatedPlaylists", {}).get("uploads", f"UU{cid[2:]}" if cid.startswith("UC") else ""),
                "studio_url": f"https://studio.youtube.com/channel/{cid}",
                "studio_analytics_url": f"https://studio.youtube.com/channel/{cid}/analytics/tab-overview",
                "studio_content_url": f"https://studio.youtube.com/channel/{cid}/videos/upload"
            },
            "recent_videos": recent_videos,
            "analytics_summary": {
                "subscribers": subs,
                "total_views": views,
                "total_videos": vids
            },
            "synced_at": datetime.now().isoformat()
        }

    # ---- Video Upload ----
    def upload_video_resumable(
        self,
        video_path: str,
        title: str,
        description: str = "",
        tags: list = None,
        category: str = "22",
        privacy: str = "private",
        thumbnail_path: Optional[str] = None,
        progress_callback: Optional[callable] = None,
        chunk_size: int = 256 * 1024 * 8  # 2MB chunks (multiple of 256KB)
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Uploads a video to YouTube using the YouTube Data API v3 Resumable Upload protocol.

        Returns:
            Tuple of (success: bool, video_id: Optional[str], error_message: Optional[str])
        """
        if not self.access_token:
            return False, None, "OAuth access token is required for YouTube Data API video uploads"

        if not os.path.exists(video_path):
            return False, None, f"Video file not found: {video_path}"

        total_size = os.path.getsize(video_path)
        if total_size == 0:
            return False, None, "Video file is empty (0 bytes)"

        # 1. Initiate Resumable Upload
        init_url = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Length": str(total_size),
            "X-Upload-Content-Type": "video/*"
        }
        metadata_body = {
            "snippet": {
                "title": title or os.path.splitext(os.path.basename(video_path))[0],
                "description": description or "",
                "tags": tags or [],
                "categoryId": str(category or "22")
            },
            "status": {
                "privacyStatus": privacy or "private",
                "selfDeclaredMadeForKids": False
            }
        }

        try:
            init_resp = self.session.post(init_url, headers=headers, json=metadata_body, timeout=60)
            if init_resp.status_code not in (200, 201):
                err_text = init_resp.text
                try:
                    err_json = init_resp.json()
                    err_text = err_json.get("error", {}).get("message", err_text)
                except Exception:
                    pass
                return False, None, f"Failed to initiate YouTube upload ({init_resp.status_code}): {err_text}"

            upload_url = init_resp.headers.get("Location")
            if not upload_url:
                return False, None, "YouTube API did not return an upload Location URL"

        except Exception as e:
            return False, None, f"Network error during upload initialization: {str(e)}"

        # 2. Upload Video Chunks
        uploaded_bytes = 0
        video_id = None

        with open(video_path, "rb") as f:
            while uploaded_bytes < total_size:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                chunk_len = len(chunk)
                start_byte = uploaded_bytes
                end_byte = uploaded_bytes + chunk_len - 1

                chunk_headers = {
                    "Content-Length": str(chunk_len),
                    "Content-Range": f"bytes {start_byte}-{end_byte}/{total_size}",
                    "Content-Type": "video/*"
                }

                max_retries = 3
                chunk_success = False
                last_err = None

                for attempt in range(max_retries):
                    try:
                        chunk_resp = self.session.put(upload_url, headers=chunk_headers, data=chunk, timeout=120)
                        if chunk_resp.status_code in (200, 201):
                            chunk_success = True
                            resp_json = chunk_resp.json()
                            video_id = resp_json.get("id")
                            uploaded_bytes += chunk_len
                            if progress_callback:
                                progress_callback(100.0)
                            break
                        elif chunk_resp.status_code == 308:
                            chunk_success = True
                            uploaded_bytes += chunk_len
                            if progress_callback:
                                pct = round((uploaded_bytes / total_size) * 100.0, 1)
                                progress_callback(min(pct, 99.0))
                            break
                        elif chunk_resp.status_code == 401:
                            return False, None, "YouTube OAuth token expired during upload"
                        elif chunk_resp.status_code == 403:
                            err_msg = "YouTube API quota exceeded or upload permission denied"
                            try:
                                err_msg = chunk_resp.json().get("error", {}).get("message", err_msg)
                            except Exception:
                                pass
                            return False, None, err_msg
                        else:
                            last_err = f"HTTP {chunk_resp.status_code}: {chunk_resp.text}"
                            time.sleep(2 ** attempt)
                    except Exception as e:
                        last_err = str(e)
                        time.sleep(2 ** attempt)

                if not chunk_success:
                    return False, None, f"Failed uploading video chunk at byte {start_byte}: {last_err}"

        if not video_id:
            return False, None, "Upload completed but no video ID was returned by YouTube"

        # 3. Upload Custom Thumbnail if provided
        if thumbnail_path and os.path.exists(thumbnail_path):
            self.set_thumbnail(video_id, thumbnail_path)

        return True, video_id, None

    def set_thumbnail(self, video_id: str, thumbnail_path: str) -> bool:
        """Set a custom thumbnail for a video."""
        if not self.access_token or not thumbnail_path or not os.path.exists(thumbnail_path):
            return False
        url = f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={video_id}"
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        try:
            with open(thumbnail_path, "rb") as f:
                resp = self.session.post(url, headers=headers, data=f, timeout=60)
                return resp.status_code in (200, 201)
        except Exception:
            return False

    def upload_video(self, video_path: str, title: str, description: str = "",
                      tags: list = None, category: str = "22", privacy: str = "private",
                      channel_id: Optional[str] = None) -> Optional[dict]:
        """Convenience wrapper for video upload."""
        if self.access_token and os.path.exists(video_path):
            success, vid_id, err = self.upload_video_resumable(
                video_path=video_path,
                title=title,
                description=description,
                tags=tags,
                category=category,
                privacy=privacy
            )
            if success:
                return {"id": vid_id, "status": {"privacyStatus": privacy}}
            return {"error": "upload_failed", "message": err}

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
        return self._make_request("videos", {"part": "snippet,status"}, method="POST", params=body)


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
