"""Server-established identity, isolated from user-controlled slots/metadata."""
from contextvars import ContextVar
from hmac import compare_digest

authenticated_user = ContextVar('authenticated_user', default=None)


def resolve_identity(authorization, tokens):
    if not authorization.startswith('Bearer '):
        return None
    candidate = authorization[7:]
    for token, user_id in tokens.items():
        if token and compare_digest(candidate.encode(), token.encode()):
            return str(user_id)
    return None
