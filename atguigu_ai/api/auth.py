"""ASGI identity boundary for REST and WebSocket, without client metadata trust."""
import json
from atguigu_ai.shared.identity import authenticated_user, resolve_identity


class IdentityMiddleware:
    def __init__(self, app, tokens):
        self.app = app
        self.tokens = tokens

    async def __call__(self, scope, receive, send):
        if scope['type'] not in {'http', 'websocket'} or not self.tokens:
            return await self.app(scope, receive, send)
        path = scope.get('path', '')
        if path in {'/', '/health'}:
            return await self.app(scope, receive, send)
        headers = dict(scope.get('headers', []))
        user_id = resolve_identity(headers.get(b'authorization', b'').decode(), self.tokens)
        if not user_id:
            if scope['type'] == 'websocket':
                return await send({'type': 'websocket.close', 'code': 4401})
            body = json.dumps({'detail': 'Authentication required'}).encode()
            await send({'type': 'http.response.start', 'status': 401,
                        'headers': [(b'content-type', b'application/json')]})
            return await send({'type': 'http.response.body', 'body': body})
        # Debug/session management APIs are not an authenticated user interface.
        # Keep them closed until per-route authorization is implemented.
        if path != '/api/messages' or scope['type'] != 'http':
            if scope['type'] == 'websocket':
                return await send({'type': 'websocket.close', 'code': 4403})
            await send({'type': 'http.response.start', 'status': 403, 'headers': []})
            return await send({'type': 'http.response.body', 'body': b'Forbidden'})
        token = authenticated_user.set(user_id)
        try:
            await self.app(scope, receive, send)
        finally:
            authenticated_user.reset(token)
