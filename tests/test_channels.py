"""Tests for channel management hardening (AC-1..AC-6)."""
import json
import tempfile
import unittest
from unittest.mock import patch

from youtube_uploader_selenium.channel_manager import ChannelManager
from api import create_app


class ChannelApiTestCase(unittest.TestCase):
    """Channel CRUD hardening tests. Auth and persistence mocked to temp dir."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cm = ChannelManager(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.app = create_app('testing')
        self.client = self.app.test_client()
        # Bypass auth decorator in channels routes; inject temp-dir manager
        fake_auth = lambda f: f
        self._auth_patch = patch('api.routes.channels.require_auth', fake_auth)
        self._cm_patch = patch('api.routes.channels.get_channel_manager', lambda: self.cm)
        self._auth_patch.start()
        self._cm_patch.start()
        self.addCleanup(self._auth_patch.stop)
        self.addCleanup(self._cm_patch.stop)

    # ---- helpers ----
    def _add_account(self, email='a@b.com', name='Acc'):
        return self.cm.add_account(email=email, display_name=name, account_type='personal')

    def _create_account_via_api(self, **overrides):
        if not overrides:
            return self.client.post('/api/channels/accounts', json={})
        payload = {'email': 'a@b.com', 'display_name': 'Acc', 'account_type': 'personal'}
        payload.update(overrides)
        return self.client.post('/api/channels/accounts', json=payload)

    def _create_channel_via_api(self, account_id=None, **overrides):
        if account_id is None and not overrides:
            return self.client.post('/api/channels', json={})
        payload = {}
        if account_id is not None:
            payload['account_id'] = account_id
        if 'channel_id' not in overrides:
            payload['channel_id'] = 'UC123'
        if 'name' not in overrides:
            payload['name'] = 'Chan'
        payload.update(overrides)
        return self.client.post('/api/channels', json=payload)

    # ---- AC-1: validation -> 400 ----
    def test_ac1_create_account_invalid_payload_400(self):
        for bad in ({}, {'email': '', 'display_name': ''},
                    {'email': 'a@b.com', 'display_name': '', 'account_type': 'x'},
                    {'email': 'a@b.com', 'display_name': 'A', 'account_type': 'not-a-type'}):
            res = self._create_account_via_api(**bad)
            self.assertEqual(res.status_code, 400, f"payload {bad}")
            self.assertIn('error', res.get_json())

    def test_ac1_create_channel_invalid_payload_400(self):
        acc = self._add_account()
        for bad in ({}, {'account_id': '', 'channel_id': 'UC1', 'name': 'x'},
                    {'account_id': acc.account_id, 'channel_id': '', 'name': 'x'},
                    {'account_id': acc.account_id, 'channel_id': 'UC1', 'name': ''}):
            res = self._create_channel_via_api(**bad)
            self.assertEqual(res.status_code, 400, f"payload {bad}")

    def test_ac1_create_account_invalid_type_not_coerced(self):
        """Old behavior silently coerced bad account_type to personal; now 400."""
        res = self._create_account_via_api(account_type='nonsense')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(len(self.cm.get_all_accounts()), 0)

    # ---- AC-2: missing ids -> 404 ----
    def test_ac2_missing_account_404(self):
        res = self.client.delete('/api/channels/accounts/nope')
        self.assertEqual(res.status_code, 404)
        res = self.client.patch('/api/channels/accounts/nope', json={'display_name': 'x'})
        self.assertEqual(res.status_code, 404)

    def test_ac2_missing_channel_404(self):
        res = self.client.delete('/api/channels/nope')
        self.assertEqual(res.status_code, 404)
        res = self.client.patch('/api/channels/nope', json={'name': 'x'})
        self.assertEqual(res.status_code, 404)
        res = self.client.get('/api/channels/nope/analytics')
        self.assertEqual(res.status_code, 404)

    # ---- AC-3: unknown account_id on channel create -> 400 ----
    def test_ac3_channel_unknown_account_400(self):
        res = self._create_channel_via_api(account_id='ghost-id')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(len(self.cm.get_all_channels()), 0)
        self.assertEqual(self.cm._channels, {})  # nothing persisted

    # ---- AC-4: delete policy 409 / force cascade ----
    def test_ac4_delete_account_with_channels_409_without_force(self):
        acc = self._add_account()
        self.cm.add_channel(account_id=acc.account_id, channel_id='UC1', name='C1')
        res = self.client.delete(f'/api/channels/accounts/{acc.account_id}')
        self.assertEqual(res.status_code, 409)
        self.assertIn(acc.account_id, self.cm._accounts)
        self.assertIn('UC1', self.cm._channels)

    def test_ac4_delete_account_force_cascades(self):
        acc = self._add_account()
        self.cm.add_channel(account_id=acc.account_id, channel_id='UC1', name='C1')
        res = self.client.delete(f'/api/channels/accounts/{acc.account_id}?force=true')
        self.assertEqual(res.status_code, 200)
        self.assertNotIn(acc.account_id, self.cm._accounts)
        self.assertNotIn('UC1', self.cm._channels)
        # persisted to disk
        with open(f'{self.tmp.name}/channels.json') as f:
            data = json.load(f)
        self.assertNotIn('UC1', data)

    # ---- AC-5: PATCH partial updates ----
    def test_ac5_patch_account(self):
        acc = self._add_account()
        res = self.client.patch(f'/api/channels/accounts/{acc.account_id}',
                                json={'display_name': 'Renamed'})
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertEqual(body['display_name'], 'Renamed')
        self.assertEqual(body['email'], 'a@b.com')  # untouched
        self.assertEqual(self.cm.get_account(acc.account_id).display_name, 'Renamed')

    def test_ac5_patch_account_rejects_disallowed_fields(self):
        acc = self._add_account()
        res = self.client.patch(f'/api/channels/accounts/{acc.account_id}',
                                json={'access_token': 'evil'})
        self.assertEqual(res.status_code, 400)

    def test_ac5_patch_channel(self):
        acc = self._add_account()
        self.cm.add_channel(account_id=acc.account_id, channel_id='UC1', name='C1')
        res = self.client.patch('/api/channels/UC1', json={'name': 'NewName', 'handle': '@h'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()['name'], 'NewName')
        self.assertEqual(self.cm.get_channel('UC1').handle, '@h')

    def test_get_channel_detail(self):
        acc = self._add_account()
        self.cm.add_channel(account_id=acc.account_id, channel_id='UC999', name='Studio Master', handle='@studiomaster')
        res = self.client.get('/api/channels/UC999')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['name'], 'Studio Master')
        self.assertEqual(data['handle'], '@studiomaster')

    def test_template_crud(self):
        acc = self._add_account()
        ch = self.cm.add_channel(account_id=acc.account_id, channel_id='UC1', name='C1')
        tmpl = self.cm.add_template(channel_id='UC1', name='Preset 1', title_template='Title {video_title}')
        
        # GET single template
        res = self.client.get(f'/api/templates/{tmpl.template_id}')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()['name'], 'Preset 1')
        
        # PATCH template
        res_patch = self.client.patch(f'/api/templates/{tmpl.template_id}', json={'name': 'Preset Updated'})
        self.assertEqual(res_patch.status_code, 200)
        self.assertEqual(res_patch.get_json()['name'], 'Preset Updated')
        self.assertEqual(self.cm.get_template(tmpl.template_id).name, 'Preset Updated')

    def test_batch_patch(self):
        batch = self.cm.create_batch(channel_id='UC1', account_id='acc1', name='Batch 1', video_paths=['v1.mp4'])
        res = self.client.patch(f'/api/batches/{batch.batch_id}', json={'priority': 'high'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()['priority'], 'high')
        self.assertEqual(self.cm.get_batch(batch.batch_id).priority, 'high')

    def test_channel_studio_hub(self):
        acc = self._add_account()
        self.cm.add_channel(account_id=acc.account_id, channel_id='UC_STUDIO', name='Studio Chan', subscriber_count=1500)
        res = self.client.get('/api/channels/UC_STUDIO/studio')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('channel', data)
        self.assertEqual(data['channel']['id'], 'UC_STUDIO')
        self.assertEqual(data['channel']['subscriber_count'], 1500)


if __name__ == '__main__':
    unittest.main()