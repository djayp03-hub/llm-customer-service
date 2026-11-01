"""Single-process, per-agent/session serialization and request timing."""
import asyncio
import logging
import time
import uuid
from functools import wraps
from weakref import WeakKeyDictionary, WeakValueDictionary

logger = logging.getLogger(__name__)


def serialized_message(method):
    @wraps(method)
    async def wrapped(self, message, sender_id='default', metadata=None):
        # Each agent owns its locks; each event loop has independent asyncio locks.
        if not hasattr(self, '_session_runtime_locks'):
            self._session_runtime_locks = WeakKeyDictionary()
        locks = self._session_runtime_locks.setdefault(
            asyncio.get_running_loop(), WeakValueDictionary())
        key = str(sender_id)
        lock = locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            locks[key] = lock
        trace_id = uuid.uuid4().hex
        started = time.perf_counter()
        async with lock:
            queue_ms = (time.perf_counter() - started) * 1000
            try:
                trusted_metadata = dict(metadata or {})
                trusted_metadata['trace_id'] = trace_id
                result = await method(self, message, sender_id, trusted_metadata)
                result.metadata.update(trace_id=trace_id, queue_ms=queue_ms,
                                       duration_ms=(time.perf_counter() - started) * 1000)
                logger.info('message_complete trace_id=%s queue_ms=%.2f duration_ms=%.2f',
                            trace_id, queue_ms, result.metadata['duration_ms'])
                return result
            except Exception:
                logger.exception('message_failed trace_id=%s', trace_id)
                raise
    return wrapped


def timed_node(name, node):
    @wraps(node)
    async def wrapped(state):
        started = time.perf_counter()
        trace_id = state.get('metadata', {}).get('trace_id')
        try:
            updates = await node(state)
        except Exception:
            logger.exception('node_failed trace_id=%s node=%s', trace_id, name)
            raise
        elapsed = (time.perf_counter() - started) * 1000
        logger.info('node_complete trace_id=%s node=%s duration_ms=%.2f', trace_id, name, elapsed)
        updates['node_timings'] = state.get('node_timings', []) + [
            {'node': name, 'duration_ms': elapsed}]
        return updates
    return wrapped
