from collections import defaultdict, deque
from threading import Lock
from time import monotonic
from fastapi import HTTPException

attempts = defaultdict(deque)
lock = Lock()


def limit_auth(request) -> None:
    """Limit authentication attempts per IP in the single-process MVP."""

    key = request.client.host if request.client else "unknown"
    now = monotonic()

    with lock:

        # Remove expired entries so inactive clients do not grow memory forever.
        for address in list(attempts):

            queue = attempts[address]

            while queue and queue[0] <= now - 60:

                queue.popleft()

            if not queue:

                del attempts[address]

        queue = attempts[key]

        if len(queue) >= 15:

            raise HTTPException(429, "Too many sign-in attempts. Try again in a minute.")

        queue.append(now)

    return None
