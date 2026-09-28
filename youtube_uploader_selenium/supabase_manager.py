"""
Supabase Python client for YouTube Uploader Pro.
Provides database operations, auth, storage, and real-time subscriptions.
"""
import os
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


class SupabaseManager:
    """Manages Supabase connection and operations for YouTube Uploader Pro."""

    _instance = None

    def __init__(self, config_path: str = None):
        self.config_path = config_path or str(Path(__file__).parent.parent / 'supabase' / 'supabase.config.json')
        self.client: Optional[Client] = None
        self.db = None
        self.storage = None
        self.auth = None
        self.user_client: Optional[Client] = None
        self.config = {}
        self._load_config()
        if SUPABASE_AVAILABLE:
            self._connect()

    def _load_config(self):
        """Load Supabase configuration."""
        if os.path.exists(self.config_path):
            with open(self.config_path) as f:
                self.config = json.load(f)

    def _connect(self):
        """Connect to Supabase."""
        url = os.environ.get('SUPABASE_URL') or self.config.get('supabaseUrl')
        key = (os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or
               os.environ.get('SUPABASE_ANON_KEY') or
               os.environ.get('SUPABASE_KEY') or
               self.config.get('serviceRoleKey') or
               self.config.get('anonKey'))
        if url and key:
            try:
                import httpx
                self.client = create_client(url, key)
                anon = (os.environ.get('SUPABASE_ANON_KEY') or
                        os.environ.get('SUPABASE_KEY') or
                        self.config.get('anonKey'))
                self.user_client = create_client(url, anon) if anon else None

                # Ensure HTTP/1.1 is used across PostgREST and GoTrue Auth clients for eventlet/LibreSSL stability
                for c in (self.client, self.user_client):
                    if not c:
                        continue
                    if hasattr(c, 'postgrest') and hasattr(c.postgrest, 'session'):
                        c.postgrest.session = httpx.Client(
                            base_url=str(c.postgrest.base_url),
                            headers=c.postgrest.session.headers,
                            http2=False
                        )
                    if hasattr(c, 'auth') and hasattr(c.auth, '_http_client'):
                        auth_headers = getattr(c.auth, '_headers', {}).copy()
                        c.auth._http_client = httpx.Client(
                            headers=auth_headers,
                            follow_redirects=True,
                            http2=False
                        )

                self.db = self.client.from_('accounts')
                self.storage = self.client.storage
                self.auth = self.client.auth
                return True
            except Exception as e:
                print(f"Supabase connection error: {e}")
                return False
        return False

    @classmethod
    def get_instance(cls, config_path: str = None) -> 'SupabaseManager':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls(config_path)
        return cls._instance

    def is_connected(self) -> bool:
        """Check if connected to Supabase."""
        return self.client is not None and SUPABASE_AVAILABLE

    # ============ PROFILES ============

    def get_profiles(self, auth_user_id: Optional[str] = None) -> List[Dict]:
        """Get profiles linked to current auth user."""
        if not self.is_connected():
            return []
        try:
            uid = auth_user_id or self._get_auth_uid()
            if uid:
                result = self.client.table('profiles').select('*').eq('auth_user_id', uid).execute()
                return result.data or []
            result = self.client.table('profiles').select('*').execute()
            return result.data or []
        except Exception:
            return []

    def create_profile(self, email: str, display_name: str, avatar_url: str = None, auth_user_id: str = None) -> Optional[Dict]:
        """Create a new profile for the auth user."""
        if not self.is_connected():
            return None
        try:
            uid = auth_user_id or self._get_auth_uid()
            result = self.client.table('profiles').insert({
                'auth_user_id': uid,
                'email': email,
                'display_name': display_name,
                'avatar_url': avatar_url
            }).execute()
            return result.data[0] if result.data else None
        except Exception:
            return None

    def ensure_profile(self, auth_user_id: str, email: str, display_name: str = None) -> Optional[Dict]:
        """Get existing profile for auth_user_id, or create one if it does not exist."""
        if not self.is_connected() or not auth_user_id:
            return None
        try:
            profile = self.get_profile(auth_user_id)
            if profile:
                return profile
            name = display_name or (email.split('@')[0] if email else 'User')
            if email:
                res_email = self.client.table('profiles').select('*').eq('email', email).limit(1).execute()
                if res_email.data:
                    up = self.client.table('profiles').update({
                        'auth_user_id': auth_user_id,
                        'display_name': name
                    }).eq('id', res_email.data[0]['id']).execute()
                    return up.data[0] if up.data else res_email.data[0]
            result = self.client.table('profiles').insert({
                'auth_user_id': auth_user_id,
                'email': email,
                'display_name': name,
                'role': 'user'
            }).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"ensure_profile error: {e}")
            return None

    def get_profile(self, auth_user_id: Optional[str] = None) -> Optional[Dict]:
        """Get user's profile by auth_user_id (with dev fallback only if no auth_user_id passed)."""
        if not self.is_connected():
            return None
        try:
            uid = auth_user_id or self._get_auth_uid()
            if uid:
                result = self.client.table('profiles').select('*').eq('auth_user_id', uid).limit(1).execute()
                if result.data:
                    return result.data[0]
                return None
            # Fallback for dev / single-user environment when auth_user_id is not specified
            result = self.client.table('profiles').select('*').limit(1).execute()
            return result.data[0] if result.data else None
        except Exception:
            return None

    def _get_auth_uid(self) -> Optional[str]:
        """Get current auth user ID if available."""
        if not self.is_connected():
            return None
        try:
            session = self.client.auth.get_session()
            return session.data.get('session', {}).get('user', {}).get('id')
        except Exception:
            return None

    # ============ ACCOUNTS ============

    def get_accounts(self, auth_user_id: Optional[str] = None) -> List[Dict]:
        """Get all accounts for user's profile."""
        if not self.is_connected():
            return []
        try:
            profile = self.get_profile(auth_user_id)
            if not profile:
                return []
            result = self.client.table('accounts').select('*').eq('profile_id', profile['id']).execute()
            return result.data or []
        except Exception:
            return []

    def create_account(self, email: str, display_name: str, account_type: str = 'personal', auth_user_id: Optional[str] = None) -> Optional[Dict]:
        """Create a new account for user's profile."""
        return self.add_account(email, display_name, account_type, auth_user_id=auth_user_id)

    def add_account(self, email: str, display_name: str, account_type: str = 'personal', google_access_token: str = None, google_refresh_token: str = None, auth_user_id: Optional[str] = None) -> Optional[Dict]:
        """Add a new account to the user's profile."""
        if not self.is_connected():
            return None
        try:
            profile = self.get_profile(auth_user_id)
            if not profile:
                return None
            data = {
                'email': email,
                'display_name': display_name,
                'account_type': account_type,
                'profile_id': profile['id']
            }
            if google_access_token:
                data['google_access_token'] = google_access_token
            if google_refresh_token:
                data['google_refresh_token'] = google_refresh_token
            result = self.client.table('accounts').insert(data).execute()
            return result.data[0] if result.data else None
        except Exception:
            return None

    def get_account(self, account_id: str) -> Optional[Dict]:
        """Get account by ID (only if owned by current profile)."""
        if not self.is_connected():
            return None
        try:
            result = self.client.table('accounts').select('*').eq('id', account_id).execute()
            if result.data and self._account_belongs_to_profile(result.data[0]):
                return result.data[0]
            return None
        except:
            return None

    def update_account(self, account_id: str, data: Dict) -> Optional[Dict]:
        """Update account (only if owned by current profile)."""
        if not self.is_connected():
            return None
        try:
            account = self.get_account(account_id)
            if not account:
                return None
            result = self.client.table('accounts').update(data).eq('id', account_id).execute()
            return result.data[0] if result.data else None
        except:
            return None

    def _account_belongs_to_profile(self, account: Dict) -> bool:
        """Check if an account belongs to the current profile."""
        profile = self.get_profile()
        if not profile:
            return False
        return account.get('profile_id') == profile['id']

    def get_accounts_by_profile(self, profile_id: str) -> List[Dict]:
        """Get all accounts for a specific profile."""
        if not self.is_connected():
            return []
        try:
            result = self.client.table('accounts').select('*').eq('profile_id', profile_id).execute()
            return result.data or []
        except:
            return []

    def delete_account(self, account_id: str) -> bool:
        """Delete an account if owned by current profile."""
        if not self.is_connected():
            return False
        try:
            account = self.get_account(account_id)
            if not account:
                return False
            self.client.table('accounts').delete().eq('id', account_id).execute()
            return True
        except:
            return False

    # ============ PROFILE CONNECTIONS ============

    def get_profile_connections(self) -> List[Dict]:
        """Get all profile connections for current user."""
        if not self.is_connected():
            return []
        try:
            profile = self.get_profile()
            if not profile:
                return []
            result = self.client.table('profile_connections').select('*').eq('profile_id', profile['id']).execute()
            return result.data or []
        except:
            return []

    def add_profile_connection(self, account_id: str, connection_type: str = 'google', is_primary: bool = False) -> Optional[Dict]:
        """Add a profile connection."""
        if not self.is_connected():
            return None
        try:
            profile = self.get_profile()
            if not profile:
                return None
            result = self.client.table('profile_connections').insert({
                'profile_id': profile['id'],
                'account_id': account_id,
                'connection_type': connection_type,
                'is_primary': is_primary
            }).execute()
            return result.data[0] if result.data else None
        except:
            return None

    # ============ CHANNELS ============

    def get_channels(self, account_id: Optional[str] = None) -> List[Dict]:
        """Get channels, optionally filtered by account."""
        if not self.is_connected():
            return []
        try:
            query = self.client.table('channels').select('*')
            if account_id:
                query = query.eq('account_id', account_id)
            result = query.execute()
            return result.data or []
        except:
            return []

    def create_channel(self, account_id: str, channel_id: str, name: str, **kwargs) -> Optional[Dict]:
        """Create a channel."""
        if not self.is_connected():
            return None
        try:
            if not self._account_belongs_to_profile({'id': account_id, 'profile_id': ''}):
                return None
            data = {
                'account_id': account_id,
                'channel_id': channel_id,
                'name': name,
                **kwargs
            }
            result = self.client.table('channels').insert(data).execute()
            return result.data[0] if result.data else None
        except:
            return None

    # ============ UPLOAD JOBS ============

    def get_upload_jobs(self, status: Optional[str] = None, channel_id: Optional[str] = None) -> List[Dict]:
        """Get upload jobs with optional filters."""
        if not self.is_connected():
            return []
        try:
            query = self.client.table('upload_jobs').select('*')
            if status:
                query = query.eq('status', status)
            if channel_id:
                query = query.eq('channel_id', channel_id)
            result = query.order('created_at', desc=True).execute()
            return result.data or []
        except:
            return []

    def create_upload_job(self, channel_id: str, account_id: str, video_path: str, **kwargs) -> Optional[Dict]:
        """Create an upload job."""
        if not self.is_connected():
            return None
        try:
            if not self._account_belongs_to_profile({'id': account_id, 'profile_id': ''}):
                return None
            data = {
                'channel_id': channel_id,
                'account_id': account_id,
                'video_path': video_path,
                **kwargs
            }
            result = self.client.table('upload_jobs').insert(data).execute()
            return result.data[0] if result.data else None
        except:
            return None

    # ============ BATCH UPLOADS ============

    def create_batch(self, channel_id: str, account_id: str, name: str, video_paths: List[str], **kwargs) -> Optional[Dict]:
        """Create a batch upload."""
        if not self.is_connected():
            return None
        try:
            if not self._account_belongs_to_profile({'id': account_id, 'profile_id': ''}):
                return None
            data = {
                'channel_id': channel_id,
                'account_id': account_id,
                'name': name,
                'video_count': len(video_paths),
                'batch_data': video_paths,
                **kwargs
            }
            result = self.client.table('bulk_batches').insert(data).execute()
            return result.data[0] if result.data else None
        except:
            return None

    # ============ NOTIFICATIONS ============

    def send_notification(self, user_id: str, notification_type: str, message: str, data: Dict = None):
        """Send a notification."""
        if not self.is_connected():
            return
        try:
            self.client.table('notifications').insert({
                'user_id': user_id,
                'type': notification_type,
                'message': message,
                'data': data or {}
            }).execute()
        except:
            pass

    # ============ SETTINGS ============

    def get_settings(self) -> Optional[Dict]:
        """Get current user's settings."""
        if not self.is_connected():
            return None
        try:
            profile = self.get_profile()
            if not profile:
                return None
            result = self.client.table('settings').select('*').eq('user_id', profile['id']).execute()
            return result.data[0] if result.data else None
        except:
            return None

    def get_dashboard_stats(self) -> Dict:
        """Get dashboard statistics."""
        if not self.is_connected():
            return {}
        try:
            result = self.client.rpc('get_dashboard_stats').execute()
            return result.data[0] if result.data else {}
        except Exception:
            return {}

    # ============ AUTH ============

    def sign_up(self, email: str, password: str, display_name: str = None) -> Optional[Dict]:
        """Create a new auth user.
        Uses admin creation when available to confirm user instantly and prevent
        free-tier SMTP rate limiting, then logs the user in immediately.
        """
        self.last_auth_error = None
        if not self.user_client and not self.client:
            self.last_auth_error = "Supabase authentication service is not connected."
            return None

        # Prefer admin creation with auto-confirmation if service role key is available
        if self.client and hasattr(self.client.auth, 'admin'):
            try:
                name = display_name or email.split('@')[0]
                user_res = self.client.auth.admin.create_user({
                    'email': email,
                    'password': password,
                    'email_confirm': True,
                    'user_metadata': {'display_name': name}
                })
                # Ensure profile exists immediately
                if getattr(user_res, 'user', None):
                    self.ensure_profile(user_res.user.id, email, name)

                # Sign in with password to obtain tokens and active session
                login_dict = self.sign_in(email, password)
                if login_dict:
                    return login_dict

                return {
                    'needs_email_confirm': False,
                    'user_id': user_res.user.id if hasattr(user_res, 'user') else None,
                    'message': 'Account created successfully. Please sign in.'
                }
            except Exception as e:
                err_str = str(e)
                if "already" in err_str.lower() or "unique" in err_str.lower():
                    self.last_auth_error = "An account with this email address already exists. Please sign in."
                    return None
                print(f"admin.create_user notice: {e}, falling back to client.sign_up")

        if not self.user_client:
            self.last_auth_error = "Supabase authentication service is not connected."
            return None

        try:
            result = self.user_client.auth.sign_up({
                'email': email,
                'password': password,
                'options': {'data': {'display_name': display_name or email.split('@')[0]}}
            })
            user = getattr(result, 'user', None)
            if user and not getattr(result, 'session', None):
                return {'needs_email_confirm': True, 'user_id': user.id}
            return self._session_dict(result)
        except Exception as e:
            self.last_auth_error = str(e)
            print(f"sign_up error: {e}")
            return None

    def sign_in(self, email: str, password: str) -> Optional[Dict]:
        """Sign in an auth user with email and password."""
        self.last_auth_error = None
        if not self.user_client:
            self.last_auth_error = "Supabase authentication service is not connected."
            return None
        try:
            result = self.user_client.auth.sign_in_with_password({
                'email': email,
                'password': password
            })
            return self._session_dict(result)
        except Exception as e:
            err_msg = str(e)
            # If rejected due to unconfirmed email, auto-confirm via admin and retry
            if ("confirm" in err_msg.lower() or "not confirmed" in err_msg.lower()) and self.client and hasattr(self.client.auth, 'admin'):
                try:
                    users = self.client.auth.admin.list_users()
                    target_user = next((u for u in users if getattr(u, 'email', '').lower() == email.lower()), None)
                    if target_user:
                        self.client.auth.admin.update_user_by_id(target_user.id, {'email_confirm': True})
                        retry_res = self.user_client.auth.sign_in_with_password({'email': email, 'password': password})
                        return self._session_dict(retry_res)
                except Exception as retry_err:
                    print(f"Auto-confirm retry error: {retry_err}")

            self.last_auth_error = err_msg
            print(f"sign_in error: {e}")
            return None

    def reset_password_for_email(self, email: str) -> bool:
        """Send a password recovery email to the user via Supabase."""
        self.last_auth_error = None
        if not self.user_client:
            self.last_auth_error = "Supabase authentication service is not connected."
            return False
        try:
            self.user_client.auth.reset_password_email(email)
            return True
        except Exception as e:
            self.last_auth_error = str(e)
            print(f"reset_password_for_email error: {e}")
            return False

    def _session_dict(self, result) -> Dict:
        """Helper to extract token & user dict from auth response."""
        session = getattr(result, 'session', None)
        user = getattr(result, 'user', None)
        return {
            'access_token': session.access_token if session else None,
            'refresh_token': session.refresh_token if session else None,
            'expires_at': session.expires_at if session else None,
            'user': {'id': user.id, 'email': user.email} if user else None,
        }

    def verify_token(self, jwt: str) -> Optional[Dict]:
        """Validate a user JWT against Supabase. Returns user dict or None."""
        if not self.user_client or not jwt:
            return None
        try:
            result = self.user_client.auth.get_user(jwt)
            user = result.user if hasattr(result, 'user') else result
            if user:
                return {'id': user.id, 'email': user.email}
        except Exception:
            pass
        return None

    def set_user_context(self, jwt: str):
        """Point the user-scoped client at the caller's JWT so RLS applies."""
        if not self.user_client:
            return
        try:
            self.user_client.postgrest.auth(jwt)
        except Exception:
            pass

    def get_profile_for_user(self, auth_user_id: str) -> Optional[Dict]:
        """Fetch the profiles row for an auth user (service client)."""
        if not self.is_connected() or not auth_user_id:
            return None
        try:
            result = self.client.table('profiles').select('*').eq('auth_user_id', auth_user_id).limit(1).execute()
            return result.data[0] if result.data else None
        except Exception:
            return None


