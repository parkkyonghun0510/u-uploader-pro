import json
import os
from pathlib import Path
from typing import Optional
from datetime import datetime
from urllib.parse import quote


def load_metadata(metadata_json_path: Optional[str] = None) -> dict:
    if metadata_json_path is None:
        return {}
    try:
        with open(metadata_json_path, encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def get_video_duration(video_path: str) -> Optional[float]:
    """Get video duration using ffprobe if available."""
    try:
        import subprocess
        result = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', video_path],
            capture_output=True, text=True, timeout=10
        )
        return float(result.stdout.strip())
    except Exception:
        return None


def format_file_size(path: str) -> str:
    """Format file size to human readable."""
    try:
        size = os.path.getsize(path)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    except:
        return "Unknown"
