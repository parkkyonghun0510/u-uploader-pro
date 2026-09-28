import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class ConfigManager:
    """Manages upload profiles and configuration settings."""

    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / 'config.json'
        self.profiles_file = self.config_dir / 'profiles.json'
        self._init_files()

    def _init_files(self):
        if not self.config_file.exists():
            default_config = {
                "default_browser": "firefox",
                "auto_login": False,
                "max_retries": 3,
                "retry_delay": 10,
                "log_level": "INFO",
                "theme": "dark",
                "notifications": True,
                "auto_upload": False
            }
            self.save(default_config)

        if not self.profiles_file.exists():
            default_profiles = []
            self._save_profiles(default_profiles)

    def load(self) -> Dict:
        if self.config_file.exists():
            with open(self.config_file) as f:
                return json.load(f)
        return {}

    def save(self, config: Dict):
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def get_profiles(self) -> List[Dict]:
        if self.profiles_file.exists():
            with open(self.profiles_file) as f:
                return json.load(f)
        return []

    def save_profile(self, profile: Dict):
        profiles = self.get_profiles()
        profile['created_at'] = datetime.now().isoformat()
        profile['id'] = len(profiles) + 1
        profiles.append(profile)
        self._save_profiles(profiles)

    def delete_profile(self, profile_name: str):
        profiles = [p for p in self.get_profiles() if p.get('name') != profile_name]
        self._save_profiles(profiles)

    def get_profile(self, name: str) -> Optional[Dict]:
        for p in self.get_profiles():
            if p.get('name') == name:
                return p
        return None

    def _save_profiles(self, profiles: List[Dict]):
        with open(self.profiles_file, 'w') as f:
            json.dump(profiles, f, indent=2)
