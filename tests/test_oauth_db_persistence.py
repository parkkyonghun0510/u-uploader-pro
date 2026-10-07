"""Unit tests for OAuth database persistence and account listing on login."""
import unittest
from unittest.mock import MagicMock, patch
import tempfile

from youtube_uploader_selenium.oauth import GoogleOAuth2
from youtube_uploader_selenium.supabase_manager import SupabaseManager
from api import create_app


class OAuthDatabasePersistenceTestCase(unittest.TestCase):
    """Test OAuth flow preserves user identity and stores connected accounts in database."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.oauth = GoogleOAuth2(self.tmp.name)
        self.oauth.register_client("test_client", "test_secret", "Test App")

    def test_get_authorization_url_preserves_auth_user_id(self):
        auth_url = self.oauth.get_authorization_url("test_client", "http://localhost/callback", auth_user_id="user-12345")
        self.assertIsNotNone(auth_url)
        self.assertIn("state=", auth_url)

        # Retrieve state from url
        import urllib.parse
        parsed = urllib.parse.urlparse(auth_url)
        qs = urllib.parse.parse_qs(parsed.query)
        state = qs["state"][0]
        self.assertIn("user-12345", state)

        # Test state token lookup
        meta = self.oauth._state_tokens.get(state)
        self.assertIsNotNone(meta)
        self.assertEqual(meta.get("auth_user_id"), "user-12345")

    @patch("requests.post")
    def test_exchange_code_attaches_auth_user_id(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "access_token": "ya29.test",
            "refresh_token": "1//test",
            "expires_in": 3600
        }
        mock_post.return_value = mock_resp

        auth_url = self.oauth.get_authorization_url("test_client", "http://localhost/callback", auth_user_id="user-xyz")
        import urllib.parse
        state = urllib.parse.parse_qs(urllib.parse.urlparse(auth_url).query)["state"][0]

        with patch.object(self.oauth, "_fetch_user_info", return_value={"email": "u@gmail.com", "name": "User"}), \
             patch.object(self.oauth, "_fetch_all_youtube_channels", return_value=[{"id": "UC_test", "snippet": {"title": "Test Channel"}}]):
            token_data = self.oauth.exchange_code("mock_code", client_id="test_client", state=state)

        self.assertIsNotNone(token_data)
        self.assertEqual(token_data.get("auth_user_id"), "user-xyz")
        self.assertEqual(token_data.get("access_token"), "ya29.test")

    def test_supabase_add_account_upsert_logic(self):
        sm = SupabaseManager()
        sm.client = MagicMock()

        # Mock ensure_profile
        with patch.object(sm, "ensure_profile", return_value={"id": "profile-111", "email": "test@gmail.com"}):
            # Mock select existing accounts (first not found, then insert)
            table_mock = MagicMock()
            sm.client.table.return_value = table_mock
            
            # Select returns empty data -> insert
            table_mock.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
            table_mock.insert.return_value.execute.return_value.data = [{
                "id": "acc-uuid-1",
                "email": "test@gmail.com",
                "display_name": "Test User",
                "google_access_token": "tok123"
            }]

            acc = sm.add_account(
                email="test@gmail.com",
                display_name="Test User",
                google_access_token="tok123",
                auth_user_id="user-123"
            )
            self.assertIsNotNone(acc)
            self.assertEqual(acc["id"], "acc-uuid-1")

            # Now test update when account exists
            table_mock.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [{
                "id": "acc-uuid-1",
                "email": "test@gmail.com"
            }]
            table_mock.update.return_value.eq.return_value.execute.return_value.data = [{
                "id": "acc-uuid-1",
                "email": "test@gmail.com",
                "google_access_token": "tok_updated"
            }]

            acc2 = sm.add_account(
                email="test@gmail.com",
                display_name="Test User Updated",
                google_access_token="tok_updated",
                auth_user_id="user-123"
            )
            self.assertIsNotNone(acc2)
            self.assertEqual(acc2["google_access_token"], "tok_updated")

    def test_get_accounts_api_includes_supabase_accounts(self):
        app = create_app('testing')
        client = app.test_client()

        fake_auth = lambda f: f
        mock_sm = MagicMock()
        mock_sm.is_connected.return_value = True
        mock_sm.get_accounts.return_value = [{
            "id": "supa-acc-uuid",
            "email": "connected@gmail.com",
            "display_name": "Google User",
            "google_access_token": "ya29.valid",
            "google_refresh_token": "1//refresh",
            "google_profile_image": "https://avatar.url",
            "channels": ["UC_connected"]
        }]

        with patch('api.routes.channels.require_auth', fake_auth), \
             patch('api.routes.channels.get_supabase', return_value=mock_sm):
            res = client.get('/api/channels/accounts')
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(any(a.get("email") == "connected@gmail.com" for a in data))
            connected_acc = next(a for a in data if a.get("email") == "connected@gmail.com")
            self.assertEqual(connected_acc.get("account_id"), "supa-acc-uuid")
            self.assertEqual(connected_acc.get("has_access_token"), True)
            self.assertEqual(connected_acc.get("has_refresh_token"), True)
            self.assertNotIn("access_token", connected_acc)
            self.assertNotIn("refresh_token", connected_acc)
            self.assertEqual(connected_acc.get("channels"), ["UC_connected"])

    def test_sync_channel_with_account_id_delegates_and_returns_200(self):
        app = create_app('testing')
        client = app.test_client()

        fake_auth = lambda f: f
        mock_sm = MagicMock()
        mock_sm.is_connected.return_value = False

        mock_api = MagicMock()
        mock_api.get_my_channels.return_value = []

        with patch('api.routes.channels.require_auth', fake_auth), \
             patch('api.routes.channels.get_supabase', return_value=mock_sm), \
             patch('api.routes.youtube._get_active_youtube_api', return_value=mock_api):
            # Request sync using an account ID (e.g., oauth-chensopheaktirano@gmail.com)
            res = client.post('/api/channels/oauth-chensopheaktirano%40gmail.com/sync')
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data.get("success"))
            self.assertEqual(data.get("status"), "success")

    def test_oauth_manager_supabase_token_fallback(self):
        from youtube_uploader_selenium.oauth import OAuthManager
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            mgr = OAuthManager(config_dir=tmp_dir)
            mock_sm = MagicMock()
            mock_sm.is_connected.return_value = True
            mock_sm.get_account.return_value = {
                "id": "oauth-user@gmail.com",
                "email": "user@gmail.com",
                "display_name": "Supabase User",
                "google_access_token": "supa_tok_123",
                "google_refresh_token": "supa_ref_123",
                "google_profile_image": "https://avatar.url",
                "created_at": "2026-09-30T10:00:00"
            }

            with patch('youtube_uploader_selenium.supabase_manager.SupabaseManager', return_value=mock_sm):
                tok = mgr.get_account_token("oauth-user@gmail.com")
                self.assertIsNotNone(tok)
                self.assertEqual(tok["access_token"], "supa_tok_123")
                valid_tok = mgr.get_valid_access_token(account_id="oauth-user@gmail.com")
                self.assertEqual(valid_tok, "supa_tok_123")


if __name__ == '__main__':
    unittest.main()
