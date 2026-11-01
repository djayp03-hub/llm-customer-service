import unittest
from atguigu_ai.api.auth import IdentityMiddleware
from atguigu_ai.shared.identity import authenticated_user


class AuthTests(unittest.IsolatedAsyncioTestCase):
    async def test_auth_sets_and_resets_trusted_context(self):
        seen = []
        async def app(scope, receive, send):
            seen.append(authenticated_user.get())
        middleware = IdentityMiddleware(app, {'token': 'alice'})
        await middleware({'type': 'http', 'path': '/api/messages',
                          'headers': [(b'authorization', b'Bearer token')]}, None, None)
        self.assertEqual(seen, ['alice'])
        self.assertIsNone(authenticated_user.get())

    async def test_unauthenticated_and_diagnostic_requests_are_blocked(self):
        async def app(*args):
            self.fail('must not reach app')
        middleware = IdentityMiddleware(app, {'token': 'alice'})
        for path, headers, expected in [
            ('/api/messages', [], 401),
            ('/api/sessions/alice', [(b'authorization', b'Bearer token')], 403),
        ]:
            messages = []
            async def send(message):
                messages.append(message)
            await middleware({'type': 'http', 'path': path, 'headers': headers}, None, send)
            self.assertEqual(messages[0]['status'], expected)
