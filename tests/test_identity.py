import unittest
from atguigu_ai.shared.identity import resolve_identity


class IdentityTests(unittest.TestCase):
    def test_only_server_configured_token_establishes_identity(self):
        self.assertEqual(resolve_identity('Bearer test-token', {'test-token': 'alice'}), 'alice')
        self.assertIsNone(resolve_identity('Bearer wrong', {'test-token': 'alice'}))
        self.assertIsNone(resolve_identity('', {'test-token': 'alice'}))
        self.assertIsNone(resolve_identity('test-token', {'test-token': 'alice'}))
