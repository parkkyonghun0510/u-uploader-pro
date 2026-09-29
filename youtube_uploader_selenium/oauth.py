import json
import secrets
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict
import requests


class GoogleOAuth2:
    """Google OAuth2 handler for YouTube account connection."""

    # Google OAuth2 endpoints
    AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
    YOUTUBE_ACCOUNT_URL = "https://www.googleapis.com/youtube/v3/channels"

    # Required scopes for YouTube upload
    SCOPES = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ]

    def __init__(self, config_dir: str = "./config"):
        self.config_dir = Path(config_dir)
        self.oauth_file = self.config_dir / "oauth_clients.json"
        self._clients: Dict[str, dict] = {}
        self._state_tokens: Dict[str, dict] = {}
        self._load_clients()

    def _load_clients(self):
        """Load OAuth client credentials from file and environment variables."""
        import os
        if self.oauth_file.exists():
            try:
                with open(self.oauth_file) as f:
                    self._clients = json.load(f)
            except:
                pass

        # Load from environment variables if set (.env), unless in test mode
        if not self._is_testing():
            env_client_id = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
            env_client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()
            if env_client_id and env_client_secret and not env_client_id.startswith("YOUR_"):
                if env_client_id not in self._clients:
                    self._clients[env_client_id] = {
                        "client_id": env_client_id,
                        "client_secret": env_client_secret,
                        "name": os.environ.get("GOOGLE_APP_NAME", "YouTube Upload Pro"),
                        "created_at": "1970-01-01T00:00:00"
                    }

    def _is_testing(self) -> bool:
        """Check if running in test environment."""
        try:
            from flask import current_app
            if current_app and current_app.config.get('TESTING'):
                return True
        except:
            pass
        return False

    def is_valid_client(self, client_data: dict, allow_test: Optional[bool] = None) -> bool:
        """Check if client credentials are real and not dummy test placeholders."""
        if not client_data or not isinstance(client_data, dict):
            return False
        cid = str(client_data.get("client_id", "")).strip()
        secret = str(client_data.get("client_secret", "")).strip()
        if not cid or not secret:
            return False
        if secret in ("[OAUTH_CLIENT_SECRET]", "YOUR_CLIENT_SECRET") or secret.startswith("YOUR_") or cid.startswith("YOUR_"):
            return False
        if allow_test is None:
            allow_test = self._is_testing()
        if not allow_test:
            if cid in ("demo-client-id", "test-client-id-123.apps.googleusercontent.com"):
                return False
            if secret in ("demo-client-secret", "test-secret-456"):
                return False
        return True

    def get_valid_clients(self) -> dict:
        """Get registered clients excluding test and demo placeholders."""
        return {k: v for k, v in self._clients.items() if self.is_valid_client(v)}

    def _save_clients(self):
        """Save OAuth client credentials."""
        with open(self.oauth_file, 'w') as f:
            json.dump(self._clients, f, indent=2)

    def register_client(self, client_id: str, client_secret: str, name: str = "YouTube Upload Pro"):
        """Register a Google OAuth client."""
        self._clients[client_id] = {
            "client_id": client_id,
            "client_secret": client_secret,
            "name": name,
            "created_at": datetime.now().isoformat()
        }
        self._save_clients()

    def get_authorization_url(self, client_id: str = None, redirect_uri: str = None) -> Optional[str]:
        """Generate Google OAuth2 authorization URL."""
        valid_clients = self.get_valid_clients()

        # If client_id is provided and valid
        if client_id and client_id in self._clients:
            if not self.is_valid_client(self._clients[client_id]) and valid_clients:
                sorted_valid = sorted(valid_clients.values(), key=lambda x: x.get("created_at", ""), reverse=True)
                client_id = sorted_valid[0]["client_id"]
        else:
            candidates = valid_clients if valid_clients else self._clients
            if not candidates:
                return None
            sorted_clients = sorted(candidates.values(), key=lambda x: x.get("created_at", ""), reverse=True)
            client_id = sorted_clients[0]["client_id"]

        if not client_id or not self.is_valid_client(self._clients.get(client_id, {})):
            return None

        state = secrets.token_urlsafe(32)
        effective_redirect = self._get_redirect_uri(redirect_uri)

        self._state_tokens[state] = {
            "client_id": client_id,
            "redirect_uri": effective_redirect,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(minutes=10)).isoformat()
        }

        params = {
            "client_id": self._clients[client_id]["client_id"],
            "redirect_uri": effective_redirect,
            "response_type": "code",
            "scope": " ".join(self.SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
            "include_granted_scopes": "true"
        }

        return f"{self.AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"

    def exchange_code(self, code: str, client_id: str = None, redirect_uri: str = None, state: str = None) -> Optional[dict]:
        """Exchange authorization code for access token."""
        if not client_id and state and state in self._state_tokens:
            client_id = self._state_tokens[state].get("client_id")
            if not redirect_uri:
                redirect_uri = self._state_tokens[state].get("redirect_uri")

        if not client_id and self._clients:
            sorted_clients = sorted(self._clients.values(), key=lambda x: x.get("created_at", ""), reverse=True)
            client_id = sorted_clients[0]["client_id"]

        if not client_id or client_id not in self._clients:
            return {"error": "OAuth client not found or not configured"}

        client = self._clients[client_id]
        effective_redirect = self._get_redirect_uri(redirect_uri)

        data = {
            "code": code,
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "redirect_uri": effective_redirect,
            "grant_type": "authorization_code"
        }

        try:
            response = requests.post(self.TOKEN_URL, data=data, timeout=30)
            response.raise_for_status()
            token_data = response.json()

            # Fetch user info
            access_token = token_data.get("access_token")
            user_info = self._fetch_user_info(access_token)

            # Fetch YouTube channel info
            youtube_info = self._fetch_youtube_channel(access_token)

            token_data["user_info"] = user_info
            token_data["youtube_channel"] = youtube_info
            token_data["expires_at"] = (datetime.now() + timedelta(seconds=token_data.get("expires_in", 3600))).isoformat()

            return token_data
        except Exception as e:
            return {"error": str(e)}

    def refresh_access_token(self, refresh_token: str, client_id: Optional[str] = None) -> Optional[dict]:
        """Refresh expired access token."""
        if not client_id or client_id not in self._clients:
            valid = self.get_valid_clients()
            candidates = valid if valid else self._clients
            if candidates:
                sorted_c = sorted(candidates.values(), key=lambda x: x.get("created_at", ""), reverse=True)
                client_id = sorted_c[0]["client_id"]
            else:
                return None

        client = self._clients[client_id]

        data = {
            "refresh_token": refresh_token,
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "grant_type": "refresh_token"
        }

        try:
            response = requests.post(self.TOKEN_URL, data=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except:
            return None

    def _fetch_user_info(self, access_token: str) -> Optional[dict]:
        """Fetch user profile info."""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(self.USERINFO_URL, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except:
            return None

    def _fetch_youtube_channel(self, access_token: str) -> Optional[dict]:
        """Fetch YouTube channel details."""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            params = {"part": "snippet,statistics,brandingSettings", "mine": "true"}
            response = requests.get(self.YOUTUBE_ACCOUNT_URL, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            if data.get("items"):
                return data["items"][0]
            return None
        except:
            return None

    def _get_redirect_uri(self, custom_uri: Optional[str] = None) -> str:
        """Get the OAuth redirect URI."""
        if custom_uri:
            return custom_uri
        import os
        return os.environ.get("OAUTH_REDIRECT_URI", "http://localhost:8080/api/youtube/oauth/callback")

    def get_active_client(self, redirect_uri: str = None) -> Optional[dict]:
        """Get active OAuth client credentials status."""
        valid_clients = self.get_valid_clients()
        candidates = valid_clients if valid_clients else self._clients
        if not candidates:
            return None
        sorted_clients = sorted(candidates.values(), key=lambda x: x.get("created_at", ""), reverse=True)
        c = sorted_clients[0]
        secret = c.get("client_secret", "")
        masked_secret = f"{secret[:4]}...{secret[-4:]}" if len(secret) > 8 else "••••••••"
        return {
            "client_id": c.get("client_id"),
            "client_secret_masked": masked_secret,
            "name": c.get("name", "YouTube Upload Pro"),
            "redirect_uri": self._get_redirect_uri(redirect_uri),
            "created_at": c.get("created_at"),
            "is_valid": self.is_valid_client(c)
        }

    def get_clients(self) -> dict:
        """Get all registered OAuth clients."""
        return self._clients

    def add_demo_client(self):
        """Add a demo client for testing."""
        if not self._clients:
            self.register_client(
                client_id="demo-client-id",
                client_secret="demo-client-secret",
                name="YouTube Upload Pro Demo"
            )


class OAuthManager:
    """Manages the complete OAuth2 flow for YouTube accounts."""

    def __init__(self, config_dir: str = "./config"):
        self.config_dir = Path(config_dir)
        self.oauth_file = self.config_dir / "oauth_tokens.json"
        self._tokens: dict = {}
        self._load_tokens()

    def _load_tokens(self):
        if self.oauth_file.exists():
            try:
                with open(self.oauth_file) as f:
                    self._tokens = json.load(f)
            except:
                pass

    def _save_tokens(self):
        with open(self.oauth_file, 'w') as f:
            json.dump(self._tokens, f, indent=2)

    def save_account_token(self, account_id: str, token_data: dict):
        """Save OAuth tokens for an account."""
        self._tokens[account_id] = {
            "access_token": token_data.get("access_token"),
            "refresh_token": token_data.get("refresh_token"),
            "expires_at": token_data.get("expires_at"),
            "user_info": token_data.get("user_info"),
            "youtube_channel": token_data.get("youtube_channel"),
            "connected_at": datetime.now().isoformat()
        }
        self._save_tokens()

    def get_account_token(self, account_id: str) -> Optional[dict]:
        """Get stored tokens for an account."""
        return self._tokens.get(account_id)

    def is_token_valid(self, account_id: str) -> bool:
        """Check if stored token is still valid."""
        token = self._tokens.get(account_id)
        if not token:
            return False
        expires_at = token.get("expires_at")
        if expires_at:
            return datetime.fromisoformat(expires_at) > datetime.now()
        return True

    def remove_account_token(self, account_id: str):
        """Remove tokens for an account."""
        self._tokens.pop(account_id, None)
        self._save_tokens()

    def get_valid_access_token(self, account_id: Optional[str] = None, channel_id: Optional[str] = None, google_oauth = None) -> Optional[str]:
        """Retrieve active valid access token, auto-refreshing if expired."""
        target_id = account_id
        if not target_id and channel_id:
            for aid, tdata in self._tokens.items():
                if aid == channel_id:
                    target_id = aid
                    break
                yt_ch = tdata.get("youtube_channel")
                if isinstance(yt_ch, dict) and yt_ch.get("id") == channel_id:
                    target_id = aid
                    break

        if not target_id and self._tokens:
            latest = sorted(self._tokens.items(), key=lambda item: item[1].get('connected_at', ''), reverse=True)
            target_id = latest[0][0]

        if not target_id:
            return None

        token_entry = self._tokens.get(target_id)
        if not token_entry:
            return None

        expires_at = token_entry.get("expires_at")
        is_expired = False
        if expires_at:
            try:
                exp_dt = datetime.fromisoformat(expires_at)
                if exp_dt <= datetime.now() + timedelta(seconds=60):
                    is_expired = True
            except Exception:
                pass

        if is_expired:
            refresh_tok = token_entry.get("refresh_token")
            if refresh_tok and google_oauth:
                refreshed = google_oauth.refresh_access_token(refresh_tok)
                if refreshed and "access_token" in refreshed:
                    new_token = refreshed["access_token"]
                    expires_in = refreshed.get("expires_in", 3600)
                    new_exp = (datetime.now() + timedelta(seconds=expires_in)).isoformat()
                    token_entry["access_token"] = new_token
                    token_entry["expires_at"] = new_exp
                    self._save_tokens()
                    return new_token

        return token_entry.get("access_token")

