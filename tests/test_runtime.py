import asyncio
import unittest
from atguigu_ai.shared.session_runtime import serialized_message, timed_node


class RuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def test_node_timing_keeps_updates_and_records_each_visit(self):
        async def node(state):
            return {'value': 3}
        wrapped = timed_node('policy', node)
        first = await wrapped({'metadata': {'trace_id': 'test'}})
        second = await wrapped({'node_timings': first['node_timings']})
        self.assertEqual(second['value'], 3)
        self.assertEqual([entry['node'] for entry in second['node_timings']], ['policy', 'policy'])
        self.assertTrue(all(entry['duration_ms'] >= 0 for entry in second['node_timings']))

    async def test_same_session_updates_are_serial_and_traced(self):
        class Dummy:
            value = 0
            @serialized_message
            async def handle_message(self, message, sender_id='default', metadata=None):
                old = self.value
                await asyncio.sleep(0)
                self.value = old + 1
                return type('Response', (), {'metadata': {}})()
        agent = Dummy()
        responses = await asyncio.gather(*(agent.handle_message('x', 'alice') for _ in range(10)))
        self.assertEqual(agent.value, 10)
        self.assertEqual(len({r.metadata['trace_id'] for r in responses}), 10)
        self.assertTrue(all(r.metadata['duration_ms'] >= 0 for r in responses))

    async def test_different_sessions_do_not_block_each_other(self):
        entered = set()
        ready = asyncio.Event()
        class Dummy:
            @serialized_message
            async def handle_message(self, message, sender_id='default', metadata=None):
                entered.add(sender_id)
                if len(entered) == 2:
                    ready.set()
                await asyncio.wait_for(ready.wait(), 1)
                return type('Response', (), {'metadata': {}})()
        agent = Dummy()
        await asyncio.gather(agent.handle_message('x', 'alice'), agent.handle_message('x', 'bob'))
