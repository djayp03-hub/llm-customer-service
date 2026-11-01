"""Transactional cancellation. No model or dialogue-state dependencies."""
from datetime import datetime
from sqlalchemy import select, update


def cancel_order(sessions, order_model, order_id, user_id):
    """Cancel only an owned, cancellable order; repeated calls do not rewrite it.

    The conditional UPDATE is the state transition boundary. Database failures
    propagate and the transaction context rolls back. No refund is performed.
    """
    if not user_id:
        return 'unauthenticated'
    with sessions.begin() as session:
        changed = session.execute(
            update(order_model)
            .where(order_model.order_id == order_id,
                   order_model.user_id == str(user_id),
                   order_model.order_status.in_(['待支付', '待发货']))
            .values(order_status='已取消', complete_time=datetime.now())
        ).rowcount
        if changed:
            return 'cancelled'
        status = session.execute(
            select(order_model.order_status).where(
                order_model.order_id == order_id,
                order_model.user_id == str(user_id))
        ).scalar_one_or_none()
        if status is None:
            return 'not_found'
        return 'already_cancelled' if status == '已取消' else 'conflict'
