import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from fastapi.testclient import TestClient
from atguigu_ai.api.server import AtguiguServer
from atguigu_ai.shared.identity import authenticated_user


class ServerAuthTests(unittest.TestCase):
    def test_client_metadata_cannot_override_server_identity(self):
        seen = []
        class Agent:
            async def handle_message(self, **kwargs):
                seen.append(authenticated_user.get())
                return SimpleNamespace(messages=[{'text': 'ok'}])
        with patch.dict(os.environ, {'CUSTOMER_SERVICE_API_TOKENS': '{"test-token":"alice"}'}):
            client = TestClient(AtguiguServer(agent=Agent()).app)
        self.assertEqual(client.post('/api/messages', json={'sender': 'alice', 'message': 'hi'}).status_code, 401)
        headers = {'Authorization': 'Bearer test-token'}
        self.assertEqual(client.post('/api/messages', headers=headers,
            json={'sender': 'bob', 'message': 'hi'}).status_code, 403)
        response = client.post('/api/messages', headers=headers, json={
            'sender': 'alice', 'message': 'hi', 'metadata': {'user_id': 'bob'}})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(seen, ['alice'])
