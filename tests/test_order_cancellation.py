import unittest
from datetime import datetime
from sqlalchemy import create_engine, String, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from ecs_demo.order_service import cancel_order


class Base(DeclarativeBase):
    pass


class Order(Base):
    __tablename__ = 'orders'
    order_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String)
    order_status: Mapped[str] = mapped_column(String)
    complete_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class CancellationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://')
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(self.engine)
        with self.sessions.begin() as session:
            session.add_all([
                Order(order_id='mine', user_id='alice', order_status='待支付'),
                Order(order_id='other', user_id='bob', order_status='待支付'),
                Order(order_id='shipped', user_id='alice', order_status='已发货'),
            ])

    def tearDown(self):
        self.engine.dispose()

    def run_cancel(self, order_id, user_id='alice'):
        return cancel_order(self.sessions, Order, order_id, user_id)

    def test_missing_identity_cannot_cancel(self):
        self.assertEqual(self.run_cancel('mine', None), 'unauthenticated')
        with self.sessions() as session:
            self.assertEqual(session.get(Order, 'mine').order_status, '待支付')

    def test_other_user_order_is_indistinguishable_from_missing(self):
        self.assertEqual(self.run_cancel('other'), 'not_found')
        self.assertEqual(self.run_cancel('missing'), 'not_found')
        with self.sessions() as session:
            self.assertEqual(session.get(Order, 'other').order_status, '待支付')

    def test_shipped_order_cannot_cancel(self):
        self.assertEqual(self.run_cancel('shipped'), 'conflict')
        with self.sessions() as session:
            self.assertEqual(session.get(Order, 'shipped').order_status, '已发货')

    def test_repeat_cancellation_preserves_completion_timestamp(self):
        self.assertEqual(self.run_cancel('mine'), 'cancelled')
        with self.sessions() as session:
            timestamp = session.get(Order, 'mine').complete_time
        self.assertEqual(self.run_cancel('mine'), 'already_cancelled')
        with self.sessions() as session:
            self.assertEqual(session.get(Order, 'mine').complete_time, timestamp)


if __name__ == '__main__':
    unittest.main()
