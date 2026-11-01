import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from ecs_demo.actions.action_order import ActionCancelOrder
from ecs_demo.actions import db_table_class
from ecs_demo import order_service
from atguigu_ai.shared.identity import authenticated_user


class CancelActionTests(unittest.IsolatedAsyncioTestCase):
    async def test_actual_action_requires_identity_and_confirmation_and_is_idempotent(self):
        engine = create_engine('sqlite://', poolclass=StaticPool,
                               connect_args={'check_same_thread': False})
        sessions = sessionmaker(engine)
        Order = db_table_class.OrderInfo
        Order.__table__.create(engine)
        with sessions.begin() as session:
            session.add(Order(order_id='one', user_id='alice', receive_id='address',
                              order_status='待支付', create_time=datetime.now()))
        slots = {'order_id': 'one', 'user_id': 'bob', 'if_cancel_order': True}
        tracker = SimpleNamespace(get_slot=slots.get)
        modules = {'actions.db': SimpleNamespace(SessionLocal=sessions),
                   'actions.db_table_class': db_table_class, 'order_service': order_service}
        try:
            with patch.dict('sys.modules', modules):
                result = await ActionCancelOrder().run(tracker)
                self.assertFalse(result.success)
                self.assertEqual(result.metadata['operation_status'], 'unauthenticated')
                token = authenticated_user.set('alice')
                try:
                    slots['if_cancel_order'] = False
                    self.assertFalse((await ActionCancelOrder().run(tracker)).success)
                    slots['if_cancel_order'] = True
                    first = await ActionCancelOrder().run(tracker)
                    second = await ActionCancelOrder().run(tracker)
                    self.assertEqual(first.metadata['operation_status'], 'cancelled')
                    self.assertEqual(second.metadata['operation_status'], 'already_cancelled')
                finally:
                    authenticated_user.reset(token)
        finally:
            engine.dispose()
