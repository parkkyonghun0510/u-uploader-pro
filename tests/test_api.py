"""Unit tests for the modular Flask API."""
import unittest
import tempfile
import shutil
from api import create_app
from api.services.manager_service import get_config_manager, get_upload_queue, reset_managers


class ApiTestCase(unittest.TestCase):
    """Test suite for modular Flask API endpoints."""

    def setUp(self):
        reset_managers()
        self.test_dir = tempfile.mkdtemp()
        self.app = create_app('testing')
        self.app.config['CONFIG_DIR'] = self.test_dir
        self.client = self.app.test_client()

    def tearDown(self):
        reset_managers()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_routes_count(self):
        """Verify that all 53 expected routes are registered."""
        rules = list(self.app.url_map.iter_rules())
        self.assertGreaterEqual(len(rules), 53)

    def test_index_page(self):
        """Verify that the index route loads the dashboard HTML."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_health_check(self):
        """Verify that the health check endpoint returns 200 and healthy status."""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data.get('status'), 'healthy')
        self.assertIn('timestamp', data)

    def test_supabase_health(self):
        """Verify that supabase health returns healthy or degraded status."""
        response = self.client.get('/api/supabase/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('supabase_connected', data)
        self.assertIn('status', data)

    def test_protected_routes_require_auth(self):
        """Protected routes must return 401 when no token is provided."""
        protected_get_endpoints = [
            '/api/jobs',
            '/api/history',
            '/api/config',
            '/api/profiles',
            '/api/channels',
            '/api/channels/accounts',
            '/api/templates',
            '/api/batches',
            '/api/auth/me',
            '/api/supabase/stats',
            '/api/supabase/profile',
            '/api/supabase/accounts',
            '/api/supabase/connections',
            '/api/supabase/dashboard',
        ]
        for endpoint in protected_get_endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(
                response.status_code, 401,
                f"Endpoint {endpoint} was expected to return 401 Unauthorized"
            )

        post_res = self.client.post('/api/supabase/sync')
        self.assertEqual(post_res.status_code, 401)

    def test_auth_signup_validation(self):
        """Signup requires valid email and password with length >= 8."""
        # Invalid email
        res = self.client.post('/api/auth/signup', json={'email': 'invalid', 'password': 'short'})
        self.assertEqual(res.status_code, 400)

        # Short password
        res = self.client.post('/api/auth/signup', json={'email': 'test@example.com', 'password': '123'})
        self.assertEqual(res.status_code, 400)

    def test_auth_forgot_password_validation(self):
        """Forgot password requires a valid email."""
        # Empty payload
        res = self.client.post('/api/auth/forgot-password', json={})
        self.assertEqual(res.status_code, 400)

        # Invalid email
        res = self.client.post('/api/auth/forgot-password', json={'email': 'not-an-email'})
        self.assertEqual(res.status_code, 400)
        self.assertIn('valid email', res.get_json().get('error', '').lower())

    def test_app_py_backward_compatibility(self):
        """Verify app.py exports remain fully backward compatible."""
        import app
        self.assertIsNotNone(app.app)
        self.assertIsNotNone(app.socketio)
        self.assertIsNotNone(app.logger)
        self.assertTrue(callable(app.start_web_app))
        self.assertTrue(callable(app.get_config_manager))
        self.assertTrue(callable(app.get_upload_queue))

    def test_oauth_config_and_registration(self):
        """Verify OAuth configuration retrieval and registration endpoints."""
        res = self.client.get('/api/youtube/oauth/config')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('configured', data)
        self.assertIn('redirect_uri', data)

        # Register a client
        reg_res = self.client.post('/api/youtube/oauth/register', json={
            'client_id': 'test-client-id-123.apps.googleusercontent.com',
            'client_secret': 'test-secret-456',
            'name': 'Test Client'
        })
        self.assertEqual(reg_res.status_code, 200)
        reg_data = reg_res.get_json()
        self.assertEqual(reg_data.get('client_id'), 'test-client-id-123.apps.googleusercontent.com')

        # Check config reflects the configured client
        res_after = self.client.get('/api/youtube/oauth/config')
        self.assertEqual(res_after.status_code, 200)
        data_after = res_after.get_json()
        self.assertTrue(data_after.get('configured'))
        self.assertEqual(data_after.get('client', {}).get('client_id'), 'test-client-id-123.apps.googleusercontent.com')

    def test_browser_profiles_endpoint(self):
        """Verify browser profiles listing endpoint."""
        res = self.client.get('/api/channels/browser-profiles')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIsInstance(data, list)


if __name__ == '__main__':
    unittest.main()
